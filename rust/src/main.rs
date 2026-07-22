use anyhow::{Context, Result};
use base64::{engine::general_purpose::STANDARD, Engine as _};
use clap::Parser;
use reqwest::blocking::Client;
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION};
use serde::Serialize;
use std::fs;
use std::path::Path;

const VERSION: &str = "0.2";
const ANSI_RESET: &str = "\x1b[0m";
const ANSI_GREEN: &str = "\x1b[32m";
const ANSI_YELLOW: &str = "\x1b[33m";
const ANSI_RED: &str = "\x1b[31m";
const ANSI_CYAN: &str = "\x1b[36m";

#[derive(Parser, Debug)]
#[command(name = "webfastrecon-rs")]
#[command(about = "Minimal Rust port of WebFastRecon")]
struct Args {
    #[arg(short = 'u', long, required = true)]
    url: String,

    #[arg(short = 't', long, default_value = "auto")]
    r#type: String,

    #[arg(short = 'w', long)]
    wordlist: Option<String>,

    #[arg(short = 'T', long)]
    threads: Option<usize>,

    #[arg(short = 'o', long)]
    output: Option<String>,

    #[arg(short = 'f', long, default_value = "txt")]
    format: String,

    #[arg(short = 'a', long)]
    agent: Option<String>,

    #[arg(long, requires = "password")]
    username: Option<String>,

    #[arg(long, requires = "username")]
    password: Option<String>,

    #[arg(long, default_value_t = 5.0)]
    timeout: f64,

    #[arg(long)]
    proxy: Option<String>,

    #[arg(long)]
    follow: bool,

    #[arg(long)]
    status: Option<String>,

    #[arg(long)]
    version: bool,

    #[arg(long)]
    force: bool,

    #[arg(long)]
    topfiles: bool,

    #[arg(long = "identify-only")]
    identify_only: bool,

    #[arg(long)]
    scan: bool,
}

#[derive(Debug, Serialize)]
struct ResultEntry {
    path: String,
    url: String,
    status: Option<u16>,
}

#[derive(Debug)]
struct DetectionResult {
    primary: Option<String>,
    matches: Vec<String>,
}

#[derive(Debug)]
struct DetectionValidation {
    profile: String,
    hits: usize,
    checked: usize,
}

fn main() -> Result<()> {
    let args = Args::parse();
    if args.version {
        println!("{VERSION}");
        return Ok(());
    }

    println!("{}", get_banner());
    let requested_profile = args.r#type.to_lowercase();
    let is_auto_profile = requested_profile == "auto";
    let identify_only_mode = args.identify_only || (is_auto_profile && !args.scan);

    println!("[*] Target.............: {}", args.url);
    println!("[*] Profile............: {}", requested_profile);
    println!(
        "[*] Threads............: {}",
        args.threads
            .map_or_else(|| "1 req/s".to_string(), |threads| threads.to_string())
    );
    println!(
        "[*] Wordlist...........: {}",
        args.wordlist
            .clone()
            .unwrap_or_else(|| format!("wordlists/{}.txt", requested_profile))
    );
    println!("[*] Timeout............: {}s", args.timeout);
    if let Some(username) = args.username.as_ref() {
        println!("[*] Auth...............: Basic ({username})");
    }
    if let Some(out) = args.output.as_ref() {
        println!("[*] Report............: {out}\n");
    } else {
        println!("[*] Report............: nenhum (use -o/--output para salvar)\n");
    }

    if identify_only_mode {
        println!("[INFO] Modo identificacao apenas: nao sera feita varredura.\n");
    } else {
        println!("[INFO] Starting scan...\n");
    }

    let client = build_client(&args)?;

    let detected = detect_profiles(&client, &args.url, args.timeout);
    let validations = validate_detected_profiles(&client, &args.url, &detected.matches, args.timeout);

    let profile_for_scan = if is_auto_profile {
        if let Some(profile) = detected.primary.as_ref() {
            for item in &detected.matches {
                let validation = validations.iter().find(|v| v.profile == *item);
                if let Some(v) = validation {
                    if v.checked > 0 && v.hits == 0 {
                        println!(
                            "identified - {}{}{} {}(possible false positive: 0/{}){}",
                            ANSI_GREEN,
                            item.to_uppercase(),
                            ANSI_RESET,
                            ANSI_YELLOW,
                            v.checked,
                            ANSI_RESET
                        );
                    } else {
                        println!(
                            "identified - {}{}{}",
                            ANSI_GREEN,
                            item.to_uppercase(),
                            ANSI_RESET
                        );
                    }
                } else {
                    println!(
                        "identified - {}{}{}",
                        ANSI_GREEN,
                        item.to_uppercase(),
                        ANSI_RESET
                    );
                }
            }
            profile.clone()
        } else {
            return Ok(());
        }
    } else {
        if let Some(profile) = detected.primary.as_ref() {
            if profile == &requested_profile {
                println!("Perfil confirmado: {}", profile.to_uppercase());
            } else {
                println!("\u{1b}[31mPerfil detectado diferente do solicitado.\u{1b}[0m");
                println!(
                    "Detectado: {} | Solicitado: {}",
                    profile.to_uppercase(),
                    requested_profile.to_uppercase()
                );
                println!("Prosseguindo com o perfil solicitado.");
            }
        } else if args.force {
            println!(
                "Aviso: nao foi possivel detectar automaticamente; forçando perfil solicitado: {} (--force).",
                requested_profile.to_uppercase()
            );
        }
        requested_profile.clone()
    };

    if identify_only_mode {
        let scan_profile = if is_auto_profile {
            "auto".to_string()
        } else {
            requested_profile.clone()
        };
        println!("[INFO] Para varrer diretorios e arquivos padrao identificados, execute:");
        println!(
            "cargo run -- --url \"{}\" -t {} --scan --topfiles",
            args.url, scan_profile
        );
        println!("\n[INFO] Identificacao concluida.");
        return Ok(());
    }

    let status_filter = parse_status_filter(args.status.as_deref())?;

    let mut results = Vec::new();
    let scan_profiles = if is_auto_profile {
        build_scan_profiles_by_category(&detected.matches)
    } else {
        vec![profile_for_scan.clone()]
    };

    let mut scanned_any = false;
    let mut last_category: Option<&'static str> = None;
    for scan_profile in scan_profiles {
        let paths = load_paths(&args.wordlist, &scan_profile)?;
        if paths.is_empty() {
            continue;
        }

        scanned_any = true;
        let category = scan_profile_category(&scan_profile);
        if last_category != Some(category) {
            println!("\n[SCAN CATEGORY] {}", scan_category_title(category));
            last_category = Some(category);
        }
        println!("\n[SCAN PROFILE] {}", scan_profile.to_uppercase());
        for path in paths.iter().take(20) {
            let target = join_url(&args.url, path);
            let response = client.get(&target).send();
            match response {
                Ok(resp) => {
                    let status = resp.status().as_u16();
                    let include_entry = status_filter
                        .as_ref()
                        .is_none_or(|codes| codes.contains(&status));
                    if include_entry {
                        println!("{} {}", format_status_tag(Some(status)), path);
                        results.push(ResultEntry {
                            path: path.clone(),
                            url: target,
                            status: Some(status),
                        });
                    }
                }
                Err(err) => {
                    if status_filter.is_none() {
                        println!("{} {} -> {}", format_status_tag(None), path, err);
                        results.push(ResultEntry {
                            path: path.clone(),
                            url: target,
                            status: None,
                        });
                    }
                }
            }
        }
    }

    if !scanned_any {
        println!("Nenhuma wordlist encontrada para o perfil ou arquivo fornecido.");
        return Ok(());
    }

    if args.output.is_some() {
        save_report(&args, &results)?;
    }

    Ok(())
}

fn build_scan_profiles_by_category(matches: &[String]) -> Vec<String> {
    let mut deduped: Vec<String> = Vec::new();
    for item in matches {
        if !deduped.iter().any(|existing| existing == item) {
            deduped.push(item.clone());
        }
    }

    let category_order = [
        "application",
        "framework",
        "runtime",
        "web_server",
        "unknown",
    ];

    let mut ordered = Vec::new();
    for category in category_order {
        for profile in &deduped {
            if scan_profile_category(profile) == category {
                ordered.push(profile.clone());
            }
        }
    }

    ordered
}

fn format_status_tag(status: Option<u16>) -> String {
    match status {
        Some(code) if (200..300).contains(&code) => {
            format!("{}[{}]{}", ANSI_GREEN, code, ANSI_RESET)
        }
        Some(code) if (300..400).contains(&code) => {
            format!("{}[{}]{}", ANSI_YELLOW, code, ANSI_RESET)
        }
        Some(code) if (400..600).contains(&code) => {
            format!("{}[{}]{}", ANSI_RED, code, ANSI_RESET)
        }
        Some(code) => format!("{}[{}]{}", ANSI_CYAN, code, ANSI_RESET),
        None => format!("{}[ERR]{}", ANSI_RED, ANSI_RESET),
    }
}

fn scan_profile_category(profile: &str) -> &'static str {
    match profile {
        "apache" | "nginx" | "iis" | "litespeed" | "openlitespeed" | "caddy" | "openresty"
        | "tomcat" | "jetty" | "undertow" | "cherokee" | "lighttpd" | "h2o" | "tengine"
        | "oracle_http_server" | "ibm_http_server" => "web_server",
        "php" | "aspnet" | "aspnet_core" | "jsp_servlet" | "java_ee" | "python_wsgi" | "nodejs"
        | "ruby" | "perl_cgi" | "go_http" | "coldfusion" => "runtime",
        "laravel" | "symfony" | "django" | "flask" | "fastapi" | "express" | "rails" => "framework",
        "wordpress" | "drupal" | "joomla" | "magento" | "ghost" | "moodle" | "mediawiki"
        | "jenkins" | "grafana" | "kibana" | "sonarqube" | "gitlab" | "gitea" | "portainer"
        | "phpmyadmin" | "adminer" | "webmin" | "cpanel" | "plesk" | "directadmin"
        | "prestashop" | "opencart" | "typo3" | "concrete5" | "umbraco" | "shopify"
        | "silverstripe" | "dotnetnuke" | "expressionengine" => "application",
        _ => "unknown",
    }
}

fn scan_category_title(category: &str) -> &'static str {
    match category {
        "application" => "APPLICATION/CMS",
        "framework" => "FRAMEWORK",
        "runtime" => "RUNTIME",
        "web_server" => "WEB SERVER",
        _ => "UNKNOWN",
    }
}

fn parse_status_filter(raw: Option<&str>) -> Result<Option<std::collections::HashSet<u16>>> {
    let Some(raw_codes) = raw else {
        return Ok(None);
    };

    let mut out = std::collections::HashSet::new();
    for part in raw_codes.split(',') {
        let code = part
            .trim()
            .parse::<u16>()
            .with_context(|| format!("codigo HTTP invalido em --status: {part}"))?;
        out.insert(code);
    }
    Ok(Some(out))
}

fn validate_detected_profiles(
    client: &Client,
    base_url: &str,
    matches: &[String],
    timeout: f64,
) -> Vec<DetectionValidation> {
    let mut out = Vec::new();

    for profile in matches {
        let paths = profile_validation_paths(profile);
        if paths.is_empty() {
            out.push(DetectionValidation {
                profile: profile.clone(),
                hits: 0,
                checked: 0,
            });
            continue;
        }

        let mut hits = 0usize;
        let mut checked = 0usize;
        for path in paths {
            let target = join_url(base_url, path);
            let response = client
                .get(&target)
                .timeout(std::time::Duration::from_secs_f64(timeout))
                .send();
            checked += 1;
            if let Ok(resp) = response {
                let code = resp.status().as_u16();
                if is_positive_profile_status(code) {
                    hits += 1;
                }
            }
        }

        out.push(DetectionValidation {
            profile: profile.clone(),
            hits,
            checked,
        });
    }

    out
}

fn is_positive_profile_status(status: u16) -> bool {
    matches!(status, 200..=399 | 401 | 403)
}

fn profile_validation_paths(profile: &str) -> &'static [&'static str] {
    match profile {
        "wordpress" => &["wp-admin/", "wp-login.php", "wp-content/"],
        "drupal" => &["sites/default/", "core/", "modules/"],
        "joomla" => &["administrator/", "components/", "modules/"],
        "magento" => &["app/etc/env.php", "pub/", "media/"],
        "prestashop" => &["modules/", "themes/", "admin/"],
        "opencart" => &["catalog/", "admin/", "system/"],
        "typo3" => &["typo3/", "typo3conf/", "fileadmin/"],
        "concrete5" => &["concrete/", "application/", "updates/"],
        "umbraco" => &["Umbraco/", "Umbraco_Client/", "App_Plugins/"],
        "laravel" => &["vendor/", "storage/", "bootstrap/cache/"],
        "moodle" => &["login/index.php", "course/view.php", "admin/"],
        "phpmyadmin" => &["phpmyadmin/", "pma/", "setup/"],
        "jenkins" => &["login", "manage", "whoAmI/"],
        "grafana" => &["login", "api/health", "public/build/"],
        "kibana" => &["login", "api/status", "app/home"],
        "apache" => &["server-status", "server-info", "cgi-bin/"],
        "nginx" => &["nginx_status", "stub_status", ".well-known/"],
        "iis" => &["iisstart.htm", "aspnet_client/", "web.config"],
        "tomcat" => &["manager/html", "host-manager/html", "docs/"],
        "openresty" => &[".well-known/", "nginx_status", "stub_status"],
        _ => &[],
    }
}

fn get_banner() -> String {
    let banner = r#"
      WebFastRecon            Author AdilsonSiqueira

            ██╗    ██╗███████╗██████╗
            ██║    ██║██╔════╝██╔══██╗
            ██║ █╗ ██║█████╗  ██████╔╝
            ██║███╗██║██╔══╝  ██╔══██╗
            ╚███╔███╔╝██║     ██║  ██║
            ╚══╝╚══╝ ╚═╝     ╚═╝  ╚═╝

"#;
    let lines: Vec<&str> = banner.lines().collect();
    let mut output = String::new();
    for (idx, line) in lines.iter().enumerate() {
        let shift = if lines.len() > 1 { idx as f32 / (lines.len() - 1) as f32 } else { 0.0 };
        let start = (24, 120, 240);
        let end = (240, 232, 120);
        let r = (start.0 as f32 * (1.0 - shift) + end.0 as f32 * shift) as u8;
        let g = (start.1 as f32 * (1.0 - shift) + end.1 as f32 * shift) as u8;
        let b = (start.2 as f32 * (1.0 - shift) + end.2 as f32 * shift) as u8;
        output.push_str(&format!("\x1b[38;2;{};{};{}m{}\x1b[0m\n", r, g, b, line));
    }
    output
}

fn build_client(args: &Args) -> Result<Client> {
    let mut client_builder = Client::builder().timeout(std::time::Duration::from_secs_f64(args.timeout));

    if args.follow {
        client_builder = client_builder.redirect(reqwest::redirect::Policy::limited(10));
    } else {
        client_builder = client_builder.redirect(reqwest::redirect::Policy::none());
    }

    if let Some(agent) = &args.agent {
        client_builder = client_builder.user_agent(agent.clone());
    }

    if let (Some(username), Some(password)) = (&args.username, &args.password) {
        let mut headers = HeaderMap::new();
        let encoded = STANDARD.encode(format!("{username}:{password}"));
        let auth_header = HeaderValue::from_str(&format!("Basic {encoded}"))
            .context("failed to build Authorization header for Basic Auth")?;
        headers.insert(AUTHORIZATION, auth_header);
        client_builder = client_builder.default_headers(headers);
    }

    if let Some(proxy) = &args.proxy {
        client_builder = client_builder.proxy(reqwest::Proxy::all(proxy)?);
    }

    Ok(client_builder.build()?)
}

fn detect_profiles(client: &Client, url: &str, timeout: f64) -> DetectionResult {
    let response = match client
        .get(url)
        .timeout(std::time::Duration::from_secs_f64(timeout))
        .send()
    {
        Ok(resp) => resp,
        Err(_) => {
            return DetectionResult {
                primary: None,
                matches: Vec::new(),
            }
        }
    };
    let headers = response.headers().clone();
    let body = response.text().unwrap_or_default();
    let body_lower = body.to_lowercase();
    let server = headers
        .get("server")
        .and_then(|v| v.to_str().ok())
        .unwrap_or_default()
        .to_lowercase();
    let powered = headers
        .get("x-powered-by")
        .and_then(|v| v.to_str().ok())
        .unwrap_or_default()
        .to_lowercase();
    let via = headers
        .get("via")
        .and_then(|v| v.to_str().ok())
        .unwrap_or_default()
        .to_lowercase();
    let set_cookie = headers
        .get("set-cookie")
        .and_then(|v| v.to_str().ok())
        .unwrap_or_default()
        .to_lowercase();
    let header_text = headers
        .iter()
        .map(|(name, value)| format!("{}={}", name.as_str(), value.to_str().unwrap_or_default()))
        .collect::<Vec<_>>()
        .join(" ");
    let combined = format!(
        "{} {} {} {} {} {}",
        body_lower,
        header_text.to_lowercase(),
        server,
        powered,
        via,
        set_cookie
    );

    let detection_priority: [(&str, &[&str]); 63] = [
        ("wordpress", &["wp-content/", "wp-includes/", "wp-json", "wp-admin", "wp-login.php"]),
        ("drupal", &["drupalsettings", "drupal.settings", "sites/default/files", "is-drupal"]),
        ("joomla", &["/media/system/js/", "joomla!", "option=com_"]),
        ("magento", &["mage/cookies.js", "magento", "skin/frontend"]),
        ("ghost", &["ghost/content", "ghost.io", "content=\"ghost\""]),
        ("moodle", &["moodle", "moodle-session", "course/view.php"]),
        ("mediawiki", &["mediawiki", "mw.config", "w/index.php?title="]),
        ("jenkins", &["x-jenkins", "jenkins-agent-protocols", "/login?from=%2f"]),
        ("grafana", &["grafana", "x-grafana", "public/build/grafana"]),
        ("kibana", &["kbn-name", "kibana", "kbn-version"]),
        ("sonarqube", &["sonarqube", "js/sonar", "api/system/status"]),
        ("gitlab", &["gitlab", "_gitlab_session", "assets/gitlab"]),
        ("gitea", &["gitea", "content=\"gitea\"", "_csrf"]),
        ("portainer", &["portainer", "x-portaineragent", "portainer.io"]),
        ("phpmyadmin", &["phpmyadmin", "pmahometext", "pma_"]),
        ("adminer", &["adminer", "login - adminer", "name=\"auth[server]\""]),
        ("webmin", &["webmin", "session_login.cgi", "x-webmin"]),
        ("cpanel", &["cpanel", "whm", "cpsess"]),
        ("plesk", &["plesk", "plesk-session-id", "x-plesk"]),
        ("directadmin", &["directadmin", "cmd=login", "x-directadmin"]),
        ("prestashop", &["prestashop", "modules/", "index.php?controller="]),
        ("opencart", &["route=common/home", "catalog/view/theme", "opencart"]),
        ("typo3", &["typo3", "typo3conf", "index.php?id="]),
        ("concrete5", &["concrete5", "/concrete/", "ccm.token"]),
        ("umbraco", &["umbraco", "umbraco_client", "x-umbraco"]),
        ("shopify", &["cdn.shopify.com", "x-shopify"]),
        ("silverstripe", &["silverstripe", "x-powered-by: silverstripe"]),
        ("dotnetnuke", &["dotnetnuke", "dnn", "__requestverificationtoken"]),
        ("expressionengine", &["expressionengine", "exp_last_visit", "exp_tracker"]),
        ("laravel", &["laravel", "xsrf-token", "laravel_session"]),
        ("symfony", &["symfony", "sf-toolbar", "x-debug-token"]),
        ("django", &["csrftoken", "django", "__admin_media_prefix__"]),
        ("flask", &["flask", "werkzeug", "session="]),
        ("fastapi", &["fastapi", "swagger-ui", "openapi.json"]),
        ("express", &["x-powered-by: express"]),
        ("rails", &["ruby on rails", "_rails", "actiondispatch"]),
        ("php", &["phpsessid", "x-powered-by: php"]),
        ("aspnet_core", &["asp.net core", "kestrel", "aspnetcore"]),
        ("aspnet", &["x-aspnet-version", "asp.net"]),
        ("jsp_servlet", &["jsessionid", "jsp", "servlet"]),
        ("java_ee", &["java ee", "jakarta", "jsessionid"]),
        ("python_wsgi", &["wsgi", "gunicorn", "uwsgi", "werkzeug"]),
        ("nodejs", &["node.js", "x-powered-by: express"]),
        ("ruby", &["passenger", "x-powered-by: phusion passenger"]),
        ("perl_cgi", &["perl", "cgi-bin"]),
        ("go_http", &["golang", "go-http-client", "x-go"]),
        ("coldfusion", &["coldfusion", "cfid", "cftoken"]),
        ("openresty", &["openresty"]),
        ("openlitespeed", &["openlitespeed"]),
        ("litespeed", &["litespeed"]),
        ("nginx", &["nginx"]),
        ("apache", &["apache"]),
        ("iis", &["microsoft-iis"]),
        ("caddy", &["caddy"]),
        ("tomcat", &["tomcat"]),
        ("jetty", &["jetty"]),
        ("undertow", &["undertow"]),
        ("cherokee", &["cherokee"]),
        ("lighttpd", &["lighttpd"]),
        ("h2o", &["h2o"]),
        ("tengine", &["tengine"]),
        ("oracle_http_server", &["oracle-http-server", "oracle http server"]),
        ("ibm_http_server", &["ibm_http_server", "ibm http server"]),
    ];

    let mut matched: Vec<String> = Vec::new();
    for (profile, markers) in detection_priority {
        if markers.iter().any(|marker| combined.contains(&marker.to_lowercase())) {
            matched.push(profile.to_string());
        }
    }

    // Remove detections that are too generic unless there is strong evidence.
    matched.retain(|profile| match profile.as_str() {
        "shopify" => {
            combined.contains("cdn.shopify.com")
                || combined.contains("x-shopify")
                || combined.contains("x-shopid")
                || combined.contains("shopify-checkout-api-token")
        }
        "ruby" => {
            combined.contains("passenger")
                || combined.contains("x-powered-by: phusion passenger")
                || combined.contains("_rails")
                || combined.contains("actiondispatch")
        }
        "php" => {
            combined.contains("x-powered-by: php")
                || combined.contains("phpsessid")
        }
        "express" => combined.contains("x-powered-by: express"),
        "nodejs" => {
            combined.contains("node.js")
                || combined.contains("x-powered-by: express")
                || combined.contains("x-powered-by: koa")
        }
        _ => true,
    });

    let server_blob = format!("{} {}", server, via);
    for (profile, markers) in [
        ("apache", vec!["apache"]),
        ("nginx", vec!["nginx"]),
        ("iis", vec!["microsoft-iis"]),
        ("litespeed", vec!["litespeed"]),
        ("openlitespeed", vec!["openlitespeed"]),
        ("caddy", vec!["caddy"]),
        ("openresty", vec!["openresty"]),
        ("tomcat", vec!["tomcat"]),
        ("jetty", vec!["jetty"]),
        ("undertow", vec!["undertow"]),
        ("cherokee", vec!["cherokee"]),
        ("lighttpd", vec!["lighttpd"]),
        ("h2o", vec!["h2o"]),
        ("tengine", vec!["tengine"]),
        ("oracle_http_server", vec!["oracle-http-server", "oracle http server"]),
        ("ibm_http_server", vec!["ibm_http_server", "ibm http server"]),
    ] {
        if markers.iter().any(|marker| server_blob.contains(marker)) {
            if !matched.iter().any(|item| item == profile) {
                matched.push(profile.to_string());
            }
        }
    }

    let primary = matched.first().cloned();
    DetectionResult {
        primary,
        matches: matched,
    }
}

fn load_paths(wordlist: &Option<String>, profile: &str) -> Result<Vec<String>> {
    if let Some(path) = wordlist {
        let content = fs::read_to_string(path).with_context(|| format!("failed to read wordlist {path}"))?;
        return Ok(content.lines().filter(|l| !l.trim().is_empty()).map(|l| l.trim().to_string()).collect());
    }

    let aliases: [(&str, &str); 20] = [
        ("openlitespeed", "litespeed"),
        ("openresty", "nginx"),
        ("tengine", "nginx"),
        ("oracle_http_server", "apache"),
        ("ibm_http_server", "apache"),
        ("aspnet_core", "aspnet"),
        ("java_ee", "jsp_servlet"),
        ("rails", "ruby"),
        ("fastapi", "python_wsgi"),
        ("flask", "python_wsgi"),
        ("django", "python_wsgi"),
        ("express", "nodejs"),
        ("symfony", "php"),
        ("mediawiki", "php"),
        ("adminer", "php"),
        ("webmin", "apache"),
        ("cpanel", "apache"),
        ("plesk", "apache"),
        ("directadmin", "apache"),
        ("dotnetnuke", "aspnet"),
    ];

    let alias_profile = aliases
        .iter()
        .find_map(|(name, mapped)| if *name == profile { Some(*mapped) } else { None })
        .unwrap_or(profile);

    let mut candidates = vec![
        format!("../wordlists/{profile}.txt"),
        format!("../wordlists/{alias_profile}.txt"),
    ];

    let category_fallback = match profile {
        "apache" | "nginx" | "iis" | "litespeed" | "openlitespeed" | "caddy" | "openresty" | "tomcat" | "jetty" | "undertow" | "cherokee" | "lighttpd" | "h2o" | "tengine" | "oracle_http_server" | "ibm_http_server" => {
            Some("../wordlists/generic_webserver.txt")
        }
        "php" | "aspnet" | "aspnet_core" | "jsp_servlet" | "java_ee" | "python_wsgi" | "nodejs" | "ruby" | "perl_cgi" | "go_http" | "coldfusion" => {
            Some("../wordlists/generic_runtime.txt")
        }
        "laravel" | "symfony" | "django" | "flask" | "fastapi" | "express" | "rails" => {
            Some("../wordlists/generic_framework.txt")
        }
        "wordpress" | "drupal" | "joomla" | "magento" | "ghost" | "moodle" | "mediawiki" | "jenkins" | "grafana" | "kibana" | "sonarqube" | "gitlab" | "gitea" | "portainer" | "phpmyadmin" | "adminer" | "webmin" | "cpanel" | "plesk" | "directadmin" | "prestashop" | "opencart" | "typo3" | "concrete5" | "umbraco" | "shopify" | "silverstripe" | "dotnetnuke" | "expressionengine" => {
            Some("../wordlists/generic_application.txt")
        }
        _ => None,
    };

    if let Some(generic) = category_fallback {
        candidates.push(generic.to_string());
    }

    for candidate in candidates {
        if Path::new(&candidate).exists() {
            let content = fs::read_to_string(&candidate)?;
            return Ok(content
                .lines()
                .filter(|line| !line.trim().is_empty())
                .map(|line| line.trim().to_string())
                .collect());
        }
    }

    if profile == "auto" {
        return Ok(vec!["/".to_string(), "wp-admin/".to_string(), "administrator/".to_string()]);
    }

    Ok(vec![])
}

fn join_url(base: &str, path: &str) -> String {
    let normalized = base.trim_end_matches('/').to_string() + "/";
    if path.starts_with('/') {
        format!("{}{}", normalized, path.trim_start_matches('/'))
    } else {
        format!("{}{}", normalized, path)
    }
}

fn save_report(args: &Args, results: &[ResultEntry]) -> Result<()> {
    let Some(out) = args.output.clone() else {
        return Ok(());
    };
    let parent = Path::new(&out).parent().unwrap_or_else(|| Path::new("."));
    if !parent.as_os_str().is_empty() {
        fs::create_dir_all(parent)?;
    }

    let format = args.format.to_lowercase();
    if format == "json" {
        let content = serde_json::to_string_pretty(results)?;
        fs::write(&out, content)?;
    } else if format == "html" {
        let mut rows = String::new();
        for r in results {
            rows.push_str(&format!(
                "<tr><td>{}</td><td><a href=\"{}\">{}</a></td></tr>",
                r.status.map_or_else(|| "ERR".to_string(), |status| status.to_string()),
                r.url,
                r.url
            ));
        }
        let html = format!("<html><body><table>{rows}</table></body></html>");
        fs::write(&out, html)?;
    } else {
        let content = results
            .iter()
            .map(|r| format!("{}\t{}\n", r.status.unwrap_or(0), r.url))
            .collect::<Vec<_>>()
            .join("");
        fs::write(&out, content)?;
    }

    println!("Report saved: {out}");
    Ok(())
}
