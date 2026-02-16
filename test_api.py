import unittest
from opsyield.cli.main import cli
from click.testing import CliRunner

class TestCli(unittest.TestCase):
    def test_cli_help(self):
        """Test that the CLI help command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Run cost analysis for a specific provider', result.output)

if __name__ == '__main__':
    unittest.main()
