using AuthApi.Data;
using AuthApi.Models;
using AuthApi.Services;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using System.Security.Claims;
using System.Text;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowRequestAnalyzerLocal", policy =>
    {
        policy
            .WithOrigins("http://localhost:8000")
            .WithMethods("POST")
            .AllowAnyHeader();
    });
});

builder.Services.AddOpenApi();

builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(
        builder.Configuration.GetConnectionString("DefaultConnection")
    ));

builder.Services.AddScoped<AuthService>();

var jwtKey = builder.Configuration["Jwt:Key"]!;

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,

            ValidIssuer = builder.Configuration["Jwt:Issuer"],
            ValidAudience = builder.Configuration["Jwt:Audience"],

            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(jwtKey)
            )
        };

        options.Events = new JwtBearerEvents
        {
            OnAuthenticationFailed = context =>
            {
                Console.WriteLine("JWT ERROR: " + context.Exception.Message);
                return Task.CompletedTask;
            }
        };
    });

builder.Services.AddAuthorization();

var app = builder.Build();

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    db.Database.Migrate();
}

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

//app.UseHttpsRedirection();
app.UseCors("AllowRequestAnalyzerLocal");
app.UseAuthentication();
app.UseAuthorization();

app.MapPost("/register", async (
    RegisterRequest request,
    AuthService authService) =>
{
    if (string.IsNullOrWhiteSpace(request.Username))
    {
        return Results.BadRequest("Username is required");
    }

    if (string.IsNullOrWhiteSpace(request.Password))
    {
        return Results.BadRequest("Password is required");
    }

    if (request.Password.Length < 8)
    {
        return Results.BadRequest(
            "Password must be at least 8 characters");
    }

    var user = await authService.RegisterAsync(request);

    if (user == null)
    {
        return Results.BadRequest("Username already exists");
    }

    return Results.Ok(new ProfileResponse
    {
        Id = user.Id,
        Username = user.Username
    });
});
app.MapPost("/login", async (
    LoginRequest request,
    AuthService authService) =>
{
    if (string.IsNullOrWhiteSpace(request.Username) ||
        string.IsNullOrWhiteSpace(request.Password))
    {
        return Results.BadRequest(
            "Username and password are required");
    }

    var tokens = await authService.LoginAsync(request);

    if (tokens == null)
    {
        return Results.Unauthorized();
    }

    return Results.Ok(new
    {
        accessToken = tokens.Value.AccessToken,
        refreshToken = tokens.Value.RefreshToken
    });
});
app.MapPost("/refresh", async (
    RefreshTokenRequest request,
    AuthService authService) =>
{
    if (string.IsNullOrWhiteSpace(request.RefreshToken))
    {
        return Results.BadRequest("Refresh token is required");
    }

    var accessToken = await authService.RefreshAccessTokenAsync(
        request.RefreshToken);

    if (accessToken == null)
    {
        return Results.Unauthorized();
    }

    return Results.Ok(new
    {
        accessToken
    });
});
app.MapPost("/logout", async (
    RefreshTokenRequest request,
    AuthService authService) =>
{
    if (string.IsNullOrWhiteSpace(request.RefreshToken))
    {
        return Results.BadRequest("Refresh token is required");
    }

    var revoked = await authService.RevokeRefreshTokenAsync(
        request.RefreshToken);

    if (!revoked)
    {
        return Results.NotFound("Refresh token not found");
    }

    return Results.Ok("Logged out");
});
app.MapGet("/profile", (ClaimsPrincipal user) =>
{
    var userId = user.FindFirstValue(ClaimTypes.NameIdentifier);
    var username = user.FindFirstValue(ClaimTypes.Name);

    if (userId == null || username == null)
    {
        return Results.Unauthorized();
    }

    return Results.Ok(new ProfileResponse
    {
        Id = int.Parse(userId),
        Username = username
    });
})
.RequireAuthorization();

app.Run();