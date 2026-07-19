use anyhow::{Context, Result};
use clap::Parser;
use reqwest::blocking::Client;
use serde::Serialize;
use std::fs;
use std::path::Path;

#[derive(Parser, Debug)]
#[command(name = "cmspathfinder-rs")]
#[command(about = "Minimal Rust port of CMSPathFinder")]
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

    #[arg(long, default_value_t = 5.0)]
    timeout: f64,

    #[arg(long)]
    proxy: Option<String>,

    #[arg(long)]
    follow: bool,

    #[arg(long)]
    topfiles: bool,
}

#[derive(Debug, Serialize)]
struct ResultEntry {
    path: String,
    url: String,
    status: Option<u16>,
}

fn main() -> Result<()> {
    let args = Args::parse();
    println!("{}", get_banner());
    let client = build_client(&args)?;
    let paths = load_paths(&args.wordlist, &args.r#type)?;

    println!("[*] Target.............: {}", args.url);
    println!("[*] CMS................: {}", args.r#type);
    println!("[*] Threads............: {}", args.threads.unwrap_or(1));
    println!("[*] Wordlist...........: {}", args.wordlist.clone().unwrap_or_else(|| format!("wordlists/{}.txt", args.r#type)));

    let detected = detect_profile(&client, &args.url, args.timeout);
    if let Some(profile) = detected.as_ref() {
        println!("CMS detectado: {}", profile);
    } else if args.r#type == "auto" {
        println!("Nenhum CMS conhecido foi identificado. O alvo não parece usar um CMS suportado ou a detecção falhou.");
    }

    let mut results = Vec::new();
    for path in paths.iter().take(20) {
        let target = join_url(&args.url, path);
        let response = client.get(&target).send();
        match response {
            Ok(resp) => {
                let status = resp.status().as_u16();
                println!("[{status}] {path}");
                results.push(ResultEntry {
                    path: path.clone(),
                    url: target,
                    status: Some(status),
                });
            }
            Err(err) => {
                println!("[ERR] {path} -> {err}");
                results.push(ResultEntry {
                    path: path.clone(),
                    url: target,
                    status: None,
                });
            }
        }
    }

    save_report(&args, &results)?;
    Ok(())
}

fn get_banner() -> String {
    let banner = r"CMSPathFinder           by AdilsonSiqueira
   ____ __  __ ____  ____       _   _
  / ___|  \/  / ___||  _ \ __ _| |_| |__
 | |   | |\/| \___ \| |_) / _` | __| '_ \
 | |___| |  | |___) |  __/ (_| | |_| | | |
  \____|_|  |_|____/|_|   \__,_|\__|_| |_|";

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

    if let Some(proxy) = &args.proxy {
        client_builder = client_builder.proxy(reqwest::Proxy::all(proxy)?);
    }

    Ok(client_builder.build()?)
}

fn detect_profile(client: &Client, url: &str, timeout: f64) -> Option<String> {
    let response = client.get(url).timeout(std::time::Duration::from_secs_f64(timeout)).send().ok()?;
    let headers = response.headers().clone();
    let body = response.text().ok()?;
    let body_lower = body.to_lowercase();
    let header_text = headers
        .iter()
        .map(|(name, value)| format!("{}={}", name.as_str(), value.to_str().unwrap_or_default()))
        .collect::<Vec<_>>()
        .join(" ");
    let combined = format!("{} {}", body_lower, header_text.to_lowercase());

    for (profile, marker) in [
        ("wordpress", "wordpress"),
        ("drupal", "drupal"),
        ("joomla", "joomla"),
        ("magento", "magento"),
        ("prestashop", "prestashop"),
        ("shopify", "shopify"),
        ("ghost", "ghost"),
        ("typo3", "typo3"),
        ("concrete5", "concrete5"),
        ("umbraco", "umbraco"),
        ("laravel", "laravel"),
        ("moodle", "moodle"),
    ] {
        if combined.contains(marker) {
            return Some(profile.to_string());
        }
    }

    None
}

fn load_paths(wordlist: &Option<String>, profile: &str) -> Result<Vec<String>> {
    if let Some(path) = wordlist {
        let content = fs::read_to_string(path).with_context(|| format!("failed to read wordlist {path}"))?;
        return Ok(content.lines().filter(|l| !l.trim().is_empty()).map(|l| l.trim().to_string()).collect());
    }

    let fallback = format!("../wordlists/{profile}.txt");
    if Path::new(&fallback).exists() {
        let content = fs::read_to_string(&fallback)?;
        return Ok(content.lines().filter(|l| !l.trim().is_empty()).map(|l| l.trim().to_string()).collect());
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
    let out = args.output.clone().unwrap_or_else(|| format!("../reports/target_{}.txt", args.r#type));
    let parent = Path::new(&out).parent().unwrap_or_else(|| Path::new("."));
    if !parent.as_os_str().is_empty() {
        fs::create_dir_all(parent)?;
    }

    let content = results.iter().map(|r| format!("{}\t{}\n", r.status.unwrap_or(0), r.url)).collect::<Vec<_>>().join("");
    fs::write(out, content)?;
    println!("Report saved: {}", args.output.clone().unwrap_or_else(|| format!("../reports/target_{}.txt", args.r#type)));
    Ok(())
}
