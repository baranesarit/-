# הרפתקה לילית בספרייה – סרטון לספרניות

- `scene.html` – כל האנימציה (Canvas, 1080×1920, 50 שניות). פונקציה `render(t)`.
- `render.js` – מרנדר את הפריימים עם Playwright ומקודד ל-MP4 עם ffmpeg.
- `audio.py` – פסקול מסתורי מסונתז (קופסת נגינה, פעמוני חצות, דופק לב, אפקטים).

הרצה מחדש:
```
npm i playwright-core @fontsource/heebo @fontsource/suez-one
node render.js full
python3 audio.py
ffmpeg -i video_noaudio.mp4 -i music.wav -c:v copy -c:a aac -b:a 192k -af loudnorm=I=-16:TP=-1.5 -shortest final.mp4
```
