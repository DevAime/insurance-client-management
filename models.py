from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Client(db.Model):
    __tablename__ = 'Clients'

    ID = db.Column(db.Integer, primary_key=True)
    AncCode = db.Column(db.Text)
    NumID = db.Column(db.Text)
    NIF = db.Column(db.Text)
    Nom = db.Column(db.Text)
    Prenom = db.Column(db.Text)
    DateNais = db.Column(db.Text)
    LieuNais = db.Column(db.Text)
    NomConj = db.Column(db.Text)
    NextOfKin = db.Column(db.Text)
    MobPhone = db.Column(db.Integer)
    MobPhone2 = db.Column(db.Text)
    NomAffich = db.Column(db.Text)
    Email = db.Column(db.Text)
    ComID = db.Column(db.Integer)
    Zone = db.Column(db.Text)
    Residence = db.Column(db.Text)
    AgentInt = db.Column(db.Integer)
    PaieTVA = db.Column(db.Integer)
    Valide = db.Column(db.Integer)
    SexeID = db.Column(db.Integer)
    BranchID = db.Column(db.Integer)
    NationalID = db.Column(db.Integer)
    EtatCivID = db.Column(db.Integer)
    PosCliID = db.Column(db.Integer)
    CategID = db.Column(db.Integer)
    OccupID = db.Column(db.Integer)
    CreatOn = db.Column(db.Text)
    CreatBy = db.Column(db.Integer)
    LModifBy = db.Column(db.Text)
    LModifOn = db.Column(db.Text)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}