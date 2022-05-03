# Changelog

### [v0.3.10](https://github.com/schireson/strapp/compare/v0.3.9...v0.3.10) (2022-05-03)

#### Fixes

* Fixes a bug in the 'default_give_up_retries' function ecec322

### [v0.3.9](https://github.com/schireson/strapp/compare/v0.3.8...v0.3.9) (2022-04-27)

#### Features

* Add functions(`enrich_http_error` and `push_scope`) to add more context to sentry errors. ab80b7e

### [v0.3.8](https://github.com/schireson/strapp/compare/v0.3.6...v0.3.8) (2022-04-06)

#### Features

* Add map_first to http mappers.

### [v0.3.5](https://github.com/schireson/strapp/compare/v0.3.4...v0.3.5) (2022-03-09)

#### Features

* Add deleted_at column option to model_base. b07e427
* Initial effort to make sqlalchemy plugin more correctly typecheck created_at/updated_at. 812153d

### [v0.3.4](https://github.com/schireson/strapp/compare/v0.3.3...v0.3.4) (2022-01-20)

#### Fixes

* Work around mypy caching bug. 575fc84

### [v0.3.3](https://github.com/schireson/strapp/compare/v0.3.2...v0.3.3) (2022-01-18)

#### Features

* Apply generics typing to Request/PreparedRequest. d149977

### [v0.3.2](https://github.com/schireson/strapp/compare/v0.3.0...v0.3.2) (2022-01-12)

#### Fixes

* linting issues. 1d7170d
* Agnostify datadog configuration. 7578077
* Improve managed_request and HttpClient.request typing. 4f439e0

## [v0.3.0](https://github.com/schireson/strapp/compare/v0.2.10...v0.3.0) (2022-01-11)

### [v0.2.10](https://github.com/schireson/strapp/compare/v0.2.9...v0.2.10) (2022-01-11)

#### Fixes

* Add missing py.typed. 4b0f670

### [v0.2.9](https://github.com/schireson/strapp/compare/v0.2.8...v0.2.9) (2022-01-07)

#### Fixes

* Compatibility with contextvar-based werkzeug. 57d3625
* Compatibility with sqlalchemy 1.4. ca45ea1

### [v0.2.8](https://github.com/schireson/strapp/compare/v0.2.3...v0.2.8) (2021-12-10)

#### Features

* Add HttpClient and class style requests. b3288d0

#### Fixes

* Address sqlalchemy 1.4 warning. 227b82f

### [v0.2.3](https://github.com/schireson/strapp/compare/v0.2.2...v0.2.3) (2020-08-27)

#### Features

* Expose type annotations. a6b96e9
* Accept create_engine kwargs. b4e34bd

### v0.2.2 (2020-07-27)

#### Features

* Print exceptions that happen during testing click commands. 41f581f

#### Fixes

* Dataclass version constraint for versions >=3.7. fd2ae4e
