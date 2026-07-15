import 'package:flutter_test/flutter_test.dart';
import 'package:myagent_mobile/core/config/app_config.dart';
import 'package:myagent_mobile/core/errors/app_error.dart';

void main() {
  test('configuration has versioned local defaults', () {
    expect(AppConfig.apiBaseUrl, endsWith('/api/v1'));
  });

  test('application errors expose their safe message', () {
    expect(const AppError('safe message').toString(), 'safe message');
  });
}
