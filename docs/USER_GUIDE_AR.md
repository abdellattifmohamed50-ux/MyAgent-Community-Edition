# دليل استخدام MyAgent Community Edition v3.0

## التشغيل السريع

```bash
cp .env.example .env
make setup
make migrate
make run
```

افتح `http://127.0.0.1:8000/docs`. يعمل النظام افتراضيًا بقاعدة SQLite ومزوّد
`mock`، لذلك يمكنك إنشاء حساب وتجربة المحادثة دون مفتاح مدفوع.

## التشغيل عبر Docker

```bash
docker compose up --build
```

- الواجهة البرمجية: `http://localhost:8000/api/v1`
- التوثيق: `http://localhost:8000/docs`
- واجهة الويب: `http://localhost:8080`

## إضافة مزوّد ذكاء اصطناعي

ضع المفتاح داخل ملف `.env` غير المرفوع إلى Git، ثم غيّر `DEFAULT_PROVIDER`.
المزوّدات المدعومة تشمل OpenAI وGemini وOpenRouter وAnthropic وDeepSeek وKimi
وZ.AI وOllama، بالإضافة إلى mock.

## الأمان

لا تستخدم أسرار التطوير في الإنتاج. الإنتاج يحتاج PostgreSQL وأسرارًا قوية
ونطاقات CORS تعمل عبر HTTPS. لا ترسل توكن WebSocket داخل رابط URL. راجع
`docs/SECURITY.md` و`docs/DEPLOYMENT.md` قبل النشر.

## حالة الإصدار

الشفرة واختبارات SQLite والتشغيل المحلي ناجحة، لكن قرار الإصدار الحالي
`NOT READY` حتى نجاح اختبارات Docker وPostgreSQL وFlutter، وإكمال تدقيق Python
المتصل بالإنترنت، وحزمة Electron، والنشر التجريبي. التفاصيل في `PROJECT_STATUS.md`.
