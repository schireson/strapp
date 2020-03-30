from strapp.flask import (
    create_app,
    database_callback,
    sqlalchemy_database,
    inject_db,
    json_response,
    Route,
)


config = {
    "drivername": "sqlite",
}


def test_database_injection():
    @json_response
    @inject_db
    def view(db):
        return db.execute("select 5").scalar()

    app = create_app(
        routes=[Route.to("GET", "/foo", view)],
        callbacks=[database_callback(sqlalchemy_database, config)],
    )
    with app.test_client() as client:
        response = client.get("/foo")

    assert response.json == 5
    assert response.status_code == 200


def test_database_error_recovery():
    @json_response
    @inject_db
    def view(db):
        raise ValueError()

    @json_response
    @inject_db
    def view2(db):
        return db.execute("select 5").scalar()

    app = create_app(
        routes=[Route.to("GET", "/foo", view), Route.to("GET", "/bar", view2)],
        callbacks=[database_callback(sqlalchemy_database, config)],
    )
    with app.test_client() as client:
        response = client.get("/foo")
        assert response.status_code == 500

        response = client.get("/bar")

    assert response.json == 5
    assert response.status_code == 200


def test_database_commit_on_success():
    @json_response
    @inject_db(commit_on_success=True)
    def view(db):
        db.execute("CREATE TABLE foo (id INTEGER);")
        db.execute("INSERT INTO foo (id) VALUES (9);")

    @json_response
    @inject_db
    def view2(db):
        return [row.id for row in db.execute("select id from foo;").fetchall()]

    app = create_app(
        routes=[Route.to("GET", "/foo", view), Route.to("GET", "/bar", view2)],
        callbacks=[database_callback(sqlalchemy_database, config)],
    )
    with app.test_client() as client:
        response = client.get("/foo")
    assert response.status_code == 200

    with app.test_client() as client:
        response = client.get("/bar")
    assert response.status_code == 200
    assert response.json == [9]


def test_changed_status_code():
    @json_response(status=201)
    def view():
        return 5

    app = create_app(
        routes=[Route.to("GET", "/foo", view)],
        callbacks=[database_callback(sqlalchemy_database, config)],
    )
    with app.test_client() as client:
        response = client.get("/foo")

    assert response.json == 5
    assert response.status_code == 201
