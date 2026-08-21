# AuthApi

A REST API for user authentication built with ASP.NET Core.

## Features

- User registration
- Password hashing with BCrypt
- JWT authentication
- Protected endpoints
- Access and refresh tokens
- Refresh token revocation
- PostgreSQL with Entity Framework Core

## Tech Stack

- C#
- ASP.NET Core
- Entity Framework Core
- PostgreSQL
- JWT
- BCrypt

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register a new user |
| POST | `/login` | Get access and refresh tokens |
| GET | `/profile` | Get the current user's profile |
| POST | `/refresh` | Issue a new access token |
| POST | `/logout` | Revoke a refresh token |

## Run

1. Open `AuthApi.slnx` in Visual Studio.
2. Configure `appsettings.Development.json`.
3. Apply the migrations.
4. Run the project.

## Notes

`appsettings.Development.json` is excluded from Git and should contain local database and JWT settings.