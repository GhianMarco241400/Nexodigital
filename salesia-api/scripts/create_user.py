import getpass
import sys

from sqlalchemy import text

from app.db import SessionLocal
from app.permissions import ALL_ROLES
from app.services.auth import hash_password


def _prompt_non_empty(label: str) -> str:
    while True:
        value = input(label).strip()
        if value:
            return value
        print("El valor no puede estar vacío.")


def _prompt_role() -> str:
    roles = sorted(ALL_ROLES)
    while True:
        value = input(f"Rol ({', '.join(roles)}): ").strip().lower()
        if value in ALL_ROLES:
            return value
        print("Rol inválido.")


def _prompt_password() -> str:
    while True:
        password = getpass.getpass("Contraseña (mínimo 10 caracteres): ")
        if len(password) < 10:
            print("La contraseña debe tener al menos 10 caracteres.")
            continue
        confirmation = getpass.getpass("Repite la contraseña: ")
        if password != confirmation:
            print("Las contraseñas no coinciden.")
            continue
        return password


def main() -> int:
    full_name = _prompt_non_empty("Nombre completo: ")
    email = _prompt_non_empty("Correo: ").lower()
    role = _prompt_role()

    with SessionLocal() as db:
        existing_id = db.execute(
            text("select id from staff_users where email = :email"),
            {"email": email},
        ).scalar_one_or_none()

        if existing_id is not None:
            answer = input(
                "El correo ya existe. ¿Deseas cambiarle la contraseña? (s/n): "
            ).strip().lower()
            if answer != "s":
                print("Operación cancelada.")
                return 0
            password = _prompt_password()
            db.execute(
                text(
                    "update staff_users set password_hash = :password_hash "
                    "where id = :user_id"
                ),
                {"password_hash": hash_password(password), "user_id": existing_id},
            )
            db.commit()
            print("Contraseña actualizada.")
            return 0

        password = _prompt_password()
        db.execute(
            text(
                "insert into staff_users "
                "(full_name, email, role, active, password_hash) "
                "values (:full_name, :email, :role, true, :password_hash)"
            ),
            {
                "full_name": full_name,
                "email": email,
                "role": role,
                "password_hash": hash_password(password),
            },
        )
        db.commit()
        print(f"Usuario '{email}' creado con rol '{role}'.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
