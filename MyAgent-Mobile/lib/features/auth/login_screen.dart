import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'auth_controller.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _register = false;
  bool _obscure = true;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(authControllerProvider);
    final loading = state.status == AuthStatus.loading;
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        body: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 460),
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(28),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          const _Brand(),
                          const SizedBox(height: 32),
                          if (_register) ...[
                            TextFormField(
                              controller: _name,
                              decoration: const InputDecoration(
                                labelText: 'الاسم',
                                prefixIcon: Icon(Icons.person_outline),
                              ),
                              validator: (value) =>
                                  (value?.trim().length ?? 0) < 2
                                  ? 'اكتب الاسم'
                                  : null,
                            ),
                            const SizedBox(height: 14),
                          ],
                          TextFormField(
                            controller: _email,
                            keyboardType: TextInputType.emailAddress,
                            decoration: const InputDecoration(
                              labelText: 'البريد الإلكتروني',
                              prefixIcon: Icon(Icons.alternate_email),
                            ),
                            validator: (value) =>
                                !(value?.contains('@') ?? false)
                                ? 'اكتب بريدًا صحيحًا'
                                : null,
                          ),
                          const SizedBox(height: 14),
                          TextFormField(
                            controller: _password,
                            obscureText: _obscure,
                            decoration: InputDecoration(
                              labelText: 'كلمة المرور',
                              prefixIcon: const Icon(Icons.lock_outline),
                              suffixIcon: IconButton(
                                onPressed: () =>
                                    setState(() => _obscure = !_obscure),
                                icon: Icon(
                                  _obscure
                                      ? Icons.visibility
                                      : Icons.visibility_off,
                                ),
                              ),
                            ),
                            validator: _validatePassword,
                          ),
                          if (state.error != null) ...[
                            const SizedBox(height: 14),
                            Text(
                              state.error!,
                              style: TextStyle(
                                color: Theme.of(context).colorScheme.error,
                              ),
                            ),
                          ],
                          const SizedBox(height: 22),
                          FilledButton.icon(
                            onPressed: loading ? null : _submit,
                            icon: loading
                                ? const SizedBox.square(
                                    dimension: 18,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Icon(Icons.arrow_forward),
                            label: Text(
                              _register ? 'إنشاء الحساب' : 'تسجيل الدخول',
                            ),
                          ),
                          TextButton(
                            onPressed: loading
                                ? null
                                : () => setState(() => _register = !_register),
                            child: Text(
                              _register
                                  ? 'لديك حساب؟ سجّل الدخول'
                                  : 'مستخدم جديد؟ أنشئ حسابًا',
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final controller = ref.read(authControllerProvider.notifier);
    if (_register) {
      await controller.register(_name.text, _email.text, _password.text);
    } else {
      await controller.login(_email.text, _password.text);
    }
  }

  String? _validatePassword(String? value) {
    final password = value ?? '';
    if (password.length < (_register ? 10 : 8)) {
      return 'كلمة المرور قصيرة';
    }
    if (_register &&
        (!RegExp('[A-Z]').hasMatch(password) ||
            !RegExp('[a-z]').hasMatch(password) ||
            !RegExp(r'\d').hasMatch(password) ||
            !RegExp(r'[^A-Za-z0-9]').hasMatch(password))) {
      return 'استخدم حرفًا كبيرًا وصغيرًا ورقمًا ورمزًا';
    }
    return null;
  }
}

class _Brand extends StatelessWidget {
  const _Brand();

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Container(
        width: 72,
        height: 72,
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF7557FF), Color(0xFF35D0BA)],
          ),
          borderRadius: BorderRadius.circular(24),
        ),
        child: const Icon(Icons.auto_awesome, color: Colors.white, size: 36),
      ),
      const SizedBox(height: 16),
      Text('MyAgent', style: Theme.of(context).textTheme.headlineMedium),
      const SizedBox(height: 6),
      Text(
        'عقلك الذكي المشترك على كل أجهزتك',
        style: Theme.of(context).textTheme.bodyMedium,
      ),
    ],
  );
}
