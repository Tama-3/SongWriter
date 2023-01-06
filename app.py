from flask import Flask, render_template, request, url_for, redirect, session
from song_writer import *
import os

app = Flask(__name__)

API_KEY = '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'
app.secret_key = b'5#y2L"F4Q8z\n\xec]/'


@app.route('/')
def index():
    session['title'] = get_trendword()
    return render_template('index.html', keyword=session['title'])


@app.route('/waiting_lyric')
def waiting_lyric():
    session['title'] = request.args.get('song-title')
    return render_template('waiting_lyric.html', title=session['title'])


@app.route('/writing_lyric')
def writing_lyric():
    session['lyric'] = write_lyric(title=session['title'], api_key=API_KEY)
    return redirect(url_for('waiting_song'))


@app.route('/waiting_song')
def waiting_song():
    return render_template('waiting_song.html', title=session['title'], lyric=session['lyric'].splitlines())


@app.route('/making_song')
def making_song():
    manual = {}
    session['song_url'] = make_song(title=session['title'], lyric=session['lyric'], **manual)
    return redirect(url_for('finished_page'))


@app.route('/finished_page')
def finished_page():
    return render_template(
        'finished_page.html', title=session['title'], lyric=session['lyric'].splitlines(), song_url=session['song_url'])

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
