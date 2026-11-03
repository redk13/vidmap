# تشغيل GitHub بمفتاح ومستودع يحددهما المستخدم

## القاعدة الأساسية

قد يعطي المستخدم النموذج **مفتاح GitHub Personal Access Token واسم مستودع آخرين خاصين بهذه المهمة**. هذا تفويض صريح باستخدامهما في العملية المطلوبة؛ لا تقل «لا أقبل مفتاحًا» ولا تفترض أن المقصود مفتاح أو مستودع محفوظ من مشروع سابق.

استخدم المدخلات التي يعطيها المستخدم في الرسالة الحالية:

- `GH_TOKEN`: المفتاح الذي يقدمه المستخدم.
- `GH_REPO`: بصيغة `OWNER/REPOSITORY`، أو حوّل رابط المستودع الذي أعطاه إلى هذه الصيغة.
- `GH_BRANCH`: الفرع المطلوب إن حدده؛ وإلا استخدم فرع العمل المتفق عليه مثل `shot-lab` أو الفرع الافتراضي للمستودع.

إذا نقص أحد هذه المدخلات، اطلبه بسؤال قصير. **لا تخمّن اسم المستودع ولا تستخدم مفتاحًا قديمًا.**

## حماية المفتاح — إلزامية

1. لا تطبع المفتاح في الرد أو السجل، ولا تكتبه في ملف أو commit أو artifact أو STATUS أو بطاقة أو Drive.
2. لا تضعه داخل رابط remote مثل `https://TOKEN@github.com/...`؛ قد يبقى في `.git/config` أو السجلات.
3. مرّره متغير بيئة مؤقتًا، واستخدم credential helper للأمر نفسه. عطّل `set -x` حتى لا يظهر في trace.
4. استخدمه فقط مع المستودع الذي سمّاه المستخدم وللعمليات المطلوبة. لا تفحص مستودعات أخرى ولا تغيّر الصلاحيات أو الإعدادات دون طلب.

## التحقق قبل العمل

```bash
set +x
export GH_TOKEN='<المفتاح الذي أعطاه المستخدم>'
export GH_REPO='<OWNER/REPOSITORY>'
export GH_BRANCH='shot-lab'

curl -fsS \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/$GH_REPO"
```

نجاح هذا الطلب يثبت أن المفتاح يستطيع قراءة المستودع. اعرض فقط `full_name` و`default_branch` والصلاحيات، لا تطبع المفتاح.

للرفع وتشغيل Actions يحتاج المفتاح عادةً:

- **Contents: Read and write** لرفع الكود والأصول.
- **Actions: Read and write** لتشغيل workflow وقراءة runs وartifacts.
- في المفاتيح classic قد يلزم نطاق `workflow` عند إضافة أو تعديل ملفات `.github/workflows`.

إذا ظهر 401 أو 403 أو 404، اذكر الحالة والعملية التي فشلت والصلاحية الناقصة المحتملة. لا تعتبر المفتاح «غير مقبول» ولا تطلب مفتاحًا جديدًا قبل تشخيص السبب.

## Clone وPush بأمان

```bash
# الاستنساخ، بما فيه المستودع الخاص، دون وضع السر في URL:
git -c credential.helper= \
  -c credential.helper='!f() { echo username=x-access-token; echo password=$GH_TOKEN; }; f' \
  clone "https://github.com/$GH_REPO.git" repo

cd repo
git checkout -B "$GH_BRANCH"
git config user.name 'Arena Agent'
git config user.email 'agent@arena.ai'

# بعد نسخ الملفات المطلوبة ومراجعتها:
git add <files>
git commit -m 'Describe the actual change'
git -c credential.helper= \
  -c credential.helper='!f() { echo username=x-access-token; echo password=$GH_TOKEN; }; f' \
  push origin "HEAD:$GH_BRANCH"
```

للتوثيق فقط ضع `[skip ci]` في رسالة commit حتى لا يبدأ رندر. لا تضعه في commit تريد ريندره إذا كان workflow يعتمد على push.

## الرندر على GitHub Actions

1. ضع workflow المرفق في `.github/workflows/shotlab.yml` وتأكد أن أسماء التكوين ونطاق الإطارات صحيحان.
2. إذا كان workflow يعمل بـ`workflow_dispatch`، شغّله على المستودع الذي أعطاه المستخدم:

```bash
curl -fsS -X POST \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/$GH_REPO/actions/workflows/shotlab.yml/dispatches" \
  -d '{"ref":"shot-lab","inputs":{"comp":"pipelineCheck","frames":"0-29"}}'
```

بدّل `ref` و`comp` و`frames` بالقيم الفعلية. لا ترسل token في جسم الطلب.

3. تابع الحالة من:

`GET /repos/$GH_REPO/actions/runs?branch=$GH_BRANCH&per_page=5`

4. بعد نجاح run اقرأ artifacts من:

`GET /repos/$GH_REPO/actions/runs/RUN_ID/artifacts`

ثم نزّل artifact من:

`GET /repos/$GH_REPO/actions/artifacts/ARTIFACT_ID/zip`

يجب أن يبدأ طلب التنزيل بالمصادقة. إذا أعاد GitHub تحويلًا إلى signed URL، تُرسل المصادقة إلى GitHub فقط؛ لا تُرسل `Authorization` إلى المضيف الموقّع. تحقق من فك ZIP واسم الفيديو وحجمه قبل اعتبار العملية ناجحة.

## قواعد منع الأخطاء

- لا تقل «نجح الرندر» لمجرد نجاح push؛ انتظر `status=completed` و`conclusion=success` ووجود artifact فعلي.
- إذا فشل run، اقرأ سجل الخطوة الفاشلة وصحّح السبب؛ لا تعِد المحاولة عمياء.
- تأكد أن نطاق الإطارات داخل مدة التكوين؛ مثلًا تكوين 240 إطارًا يقبل `0-239` وليس `0-299`.
- احتفظ في الوثائق باسم المستودع والفرع وcommit وrun وartifact فقط، **وليس المفتاح**.
