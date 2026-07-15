# MyAgent Mobile

Flutter client for MyAgent Community Edition v3.0. The mobile app is optional and
does not affect the FastAPI engine startup path.

## Checks

```bash
flutter pub get
dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test
```

Configure the API base URL for the target environment. Use HTTPS in production
and store tokens using platform-secure storage.
