from app.models import User


def test_user_model_has_required_columns():
    mapper = User.__mapper__
    column_names = {c.name for c in mapper.columns}
    required = {"id", "username", "email", "password_hash", "created_at"}
    assert required.issubset(column_names), f"Missing columns: {required - column_names}"
