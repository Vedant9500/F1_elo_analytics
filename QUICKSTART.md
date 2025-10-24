# Quick Start Guide - F1 ELO Rankings Web App

## 🏁 Getting Started in 5 Minutes

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Verify Database Setup
Make sure your database at `DB/f1_database.db` has:
- ✅ `drivers` table
- ✅ `results` table
- ✅ `races` table
- ✅ `constructors` table
- ✅ `driver_elo` table (created by ELO calculation script)

### Step 3: Calculate Initial ELO Ratings (if not done)
```bash
python elo_calculation/calculate_driver_elo.py
```

This will populate the `driver_elo` table with ratings for all drivers.

### Step 4: Launch the Web App
```bash
python app.py
```

### Step 5: Open in Browser
Navigate to: **http://localhost:5000**

---

## 📊 After Each Race

### Method 1: Manual Update
1. Add race results to your database
2. Run: `python update_rankings.py`
3. Refresh the web page

### Method 2: Automated (Future)
- Set up a scheduled task to fetch results automatically
- Run ELO calculation script
- Rankings update automatically

---

## 🎨 Customization Ideas

### Change Theme Colors
Edit `static/css/style.css`:
```css
:root {
    --primary-color: #e10600;  /* Change main color */
    --background-dark: #15151e;
    --background-light: #1f1f2e;
}
```

### Add New Filter Options
1. Update filter buttons in `templates/index.html`
2. Add corresponding logic in `app.py` and `static/js/app.js`

### Modify Card Design
Edit the `.driver-card` section in `static/css/style.css`

---

## 🔧 Troubleshooting

### Issue: "No rankings available"
**Solution**: Run the ELO calculation script first
```bash
python elo_calculation/calculate_driver_elo.py
```

### Issue: "Import flask could not be resolved"
**Solution**: Install Flask
```bash
pip install flask
```

### Issue: Database not found
**Solution**: Check the path in `app.py` (line 11):
```python
DB_PATH = 'DB/f1_database.db'
```

### Issue: Team colors not showing
**Solution**: Check team names match in `teamColorMap` in `static/js/app.js`

---

## 📁 File Structure Quick Reference

```
├── app.py                    ← Backend (modify API endpoints here)
├── templates/
│   └── index.html           ← HTML structure
├── static/
│   ├── css/
│   │   └── style.css       ← Styling and colors
│   └── js/
│       └── app.js          ← Frontend logic
└── update_rankings.py       ← Run after each race
```

---

## 🚀 Next Steps

1. ✅ Run the app and verify it works
2. 🎨 Customize colors and styling
3. 📊 Add more statistics and features
4. 🔄 Set up automatic data updates
5. 📱 Improve mobile responsiveness
6. 📈 Add charts and visualizations

---

## 💡 Tips

- **Development Mode**: Flask runs with auto-reload in debug mode
- **Port Change**: Edit `port=5000` in `app.py` if needed
- **Database Backup**: Always backup before running updates
- **Testing**: Use different filters to verify all time periods work

---

## 📞 Need Help?

Check the main `README.md` for detailed documentation and API reference.
