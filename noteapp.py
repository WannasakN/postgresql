import flask

import models
import forms
from datetime import datetime


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
        tag=tag,
    )

@app.route("/notes/edit/<int:note_id>", methods=["GET", "POST"])
def notes_edit(note_id):
    db = models.db
    note = db.session.query(models.Note).get(note_id)
    if not note:
        return "Note not found", 404

    form = forms.NoteForm(obj=note)
    if form.validate_on_submit():
        note.title = flask.request.form["title"]
        note.description = flask.request.form["description"]
        note.updateed_date = datetime.now()

        db.session.commit()
        return flask.redirect(flask.url_for("index"))

    return flask.render_template("notes-edit.html", form=form, note=note)

@app.route("/notes/delete/<int:note_id>")
def notes_delete(note_id):
    db = models.db
    note = db.session.query(models.Note).get(note_id)
    if not note:
        return "Note not found", 404

    db.session.delete(note)
    db.session.commit()
    return flask.redirect(flask.url_for("index"))

@app.route("/tags/edit/<int:tag_id>", methods=["GET", "POST"])
def tags_edit(tag_id):
    db = models.db
    tag = db.session.query(models.Tag).get(tag_id)
    if not tag:
        return "Tag not found", 404

    form = forms.TagForm(obj=tag)
    if flask.request.method == "POST":
        tagname = form.name.data  # เข้าถึงข้อมูลจากฟิลด์ในแบบฟอร์ม

        tag.name = tagname
        db.session.commit()
        return flask.redirect(flask.url_for("index"))

    return flask.render_template("tags-edit.html", form=form, tag=tag)

@app.route("/tags/delete/<int:tag_id>", methods=["GET", "POST"])
def tags_delete(tag_id):
    db = models.db
    tag = db.session.query(models.Tag).get(tag_id)

    if not tag:
        return "Tag not found", 404

    form = forms.TagForm(obj=tag)
    if flask.request.method == "POST":
        tag.name = flask.request.form["name"]
        related_notes = db.session.query(models.Note).filter(models.Note.tags.any(id=tag_id)).all()
        for note in related_notes:
            note.tags.remove(tag)

        db.session.delete(tag)  # ลบแท็ก
        db.session.commit()  # ยืนยันการลบ
        return flask.redirect(flask.url_for("index"))

    return flask.render_template("tags-dalete.html", tag=tag, form=form)
    


if __name__ == "__main__":
    app.run(debug=True)
