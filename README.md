# SubtlePass — אתר דוגמא

אתר דוגמא (landing page) שמדגים הטמעה של ווידג'ט תוכניות התשלום של
[SubtlePass](https://subtlepass.com).

## מה יש כאן

- `index.html` — דף נחיתה ב-RTL עברית עם hero, יתרונות, אזור תמחור ושאלות נפוצות.
- `styles.css` — עיצוב כהה ונקי, רספונסיבי.

## הווידג'ט

הווידג'ט מוטמע בעזרת שתי שורות בלבד:

```html
<div
  data-subtlepass-widget
  data-plan-id="plan_f505f0282330404c9f9da6225c78eb0f"
></div>
<script src="https://subtlepass.com/widget/v1/subtlepass.js"></script>
```

ה-`div` מסומן ב-`data-subtlepass-widget` ומקבל את מזהה התוכנית דרך
`data-plan-id`, והסקריפט של SubtlePass טוען לתוכו את כרטיס התוכנית.

## הרצה מקומית

זהו אתר סטטי — אפשר לפתוח את `index.html` ישירות בדפדפן, או להריץ שרת מקומי:

```bash
python3 -m http.server 8000
# גלשו אל http://localhost:8000
```

> הערה: טעינת הווידג'ט עצמו דורשת חיבור אינטרנט לשרת של SubtlePass.
