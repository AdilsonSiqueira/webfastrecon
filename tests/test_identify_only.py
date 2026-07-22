import unittest
from argparse import Namespace
from unittest.mock import patch

from webfastrecon import build_parser
from scanner import Scanner


class IdentifyOnlyTests(unittest.TestCase):
    def test_parser_supports_identify_only(self):
        parser = build_parser()
        args = parser.parse_args(['-u', 'https://example.com', '--identify-only'])
        self.assertTrue(args.identify_only)

    def test_scanner_skips_scan_when_identify_only(self):
        args = Namespace(
            url='https://example.com',
            type='auto',
            wordlist=None,
            threads=None,
            output=None,
            format='txt',
            agent=None,
            username=None,
            password=None,
            timeout=5.0,
            proxy=None,
            follow=False,
            status=None,
            version=False,
            force=False,
            topfiles=False,
            identify_only=True,
        )

        scanner = Scanner(args)

        with patch('scanner.fingerprint.detect_profile', return_value=('wordpress', {})):
            with patch.object(Scanner, 'load_wordlist', side_effect=AssertionError('wordlist should not be loaded')):
                scanner.run()


if __name__ == '__main__':
    unittest.main()
