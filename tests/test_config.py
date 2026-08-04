from core.engine import Engine


def test_company_config_supports_multiple_urls(tmp_path) -> None:
    config = tmp_path / "companies.yaml"
    config.write_text("companies:\n  - name: Acme\n    urls:\n      - url: https://boards.greenhouse.io/acme\n      - url: https://jobs.lever.co/acme\n")
    companies = Engine.load_companies(config)
    assert len(companies) == 1
    assert len(companies[0].urls) == 2

