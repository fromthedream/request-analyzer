FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build

WORKDIR /src

COPY AuthApi.csproj .
RUN dotnet restore AuthApi.csproj

COPY . .

RUN dotnet publish AuthApi.csproj --configuration Release --output /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime

WORKDIR /app

COPY --from=build /app/publish .

ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080

ENTRYPOINT ["dotnet", "AuthApi.dll"]
