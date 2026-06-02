from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, Date, DateTime, Double, Enum, ForeignKeyConstraint, Integer, Numeric, PrimaryKeyConstraint, String, Table, Text, Time, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import OID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime
import decimal

class Base(DeclarativeBase):
    pass


class Cases(Base):
    __tablename__ = 'cases'
    __table_args__ = (
        PrimaryKeyConstraint('caseid', name='cases_pkey'),
    )

    caseid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    casetype: Mapped[Optional[str]] = mapped_column(String(100))
    filingdate: Mapped[Optional[datetime.date]] = mapped_column(Date)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    createdat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updatedat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    
    casenumber: Mapped[Optional[str]] = mapped_column(String(100))
    is_potential_duplicate: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    duplicate_of: Mapped[Optional[int]] = mapped_column(BigInteger)

    court: Mapped[List['Court']] = relationship('Court', secondary='courtaccess', back_populates='cases')
    prosecutor: Mapped[List['Prosecutor']] = relationship('Prosecutor', secondary='prosecutorassign', back_populates='cases')
    lawyer: Mapped[List['Lawyer']] = relationship('Lawyer', secondary='caselawyeraccess', back_populates='cases')
    judge: Mapped[List['Judge']] = relationship('Judge', secondary='judgeaccess', back_populates='cases')
    caseparticipant: Mapped[List['Caseparticipant']] = relationship('Caseparticipant', secondary='caseparticipantaccess', back_populates='cases')
    appeals: Mapped[List['Appeals']] = relationship('Appeals', back_populates='cases')
    bail: Mapped[List['Bail']] = relationship('Bail', back_populates='cases')
    casehistory: Mapped[List['Casehistory']] = relationship('Casehistory', back_populates='cases')
    documentcase: Mapped[List['Documentcase']] = relationship('Documentcase', back_populates='cases')
    evidence: Mapped[List['Evidence']] = relationship('Evidence', back_populates='cases')
    finaldecision: Mapped[List['Finaldecision']] = relationship('Finaldecision', back_populates='cases')
    remands: Mapped[List['Remands']] = relationship('Remands', back_populates='cases')
    hearings: Mapped[List['Hearings']] = relationship('Hearings', back_populates='cases')
    payments: Mapped[List['Payments']] = relationship('Payments', back_populates='cases')


class Court(Base):
    __tablename__ = 'court'
    __table_args__ = (
        PrimaryKeyConstraint('courtid', name='court_pkey'),
    )

    courtid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    courtname: Mapped[Optional[str]] = mapped_column(String(255))
    type: Mapped[Optional[str]] = mapped_column(String(255))
    location: Mapped[Optional[str]] = mapped_column(String(255))

    cases: Mapped[List['Cases']] = relationship('Cases', secondary='courtaccess', back_populates='court')
    judge: Mapped[List['Judge']] = relationship('Judge', secondary='judgeworksin', back_populates='court')
    courtregistrar: Mapped[List['Courtregistrar']] = relationship('Courtregistrar', back_populates='court')
    courtroom: Mapped[List['Courtroom']] = relationship('Courtroom', back_populates='court')
    payments: Mapped[List['Payments']] = relationship('Payments', back_populates='court')


class Documents(Base):
    __tablename__ = 'documents'
    __table_args__ = (
        PrimaryKeyConstraint('documentid', name='documents_pkey'),
    )

    documentid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    documenttype: Mapped[Optional[str]] = mapped_column(String(100))
    documenttitle: Mapped[Optional[str]] = mapped_column(String(255))
    uploaddate: Mapped[Optional[datetime.date]] = mapped_column(Date)
    filepath: Mapped[Optional[str]] = mapped_column(String(500))
    createdat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updatedat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    documentcase: Mapped[List['Documentcase']] = relationship('Documentcase', back_populates='documents')


t_pg_stat_statements = Table(
    'pg_stat_statements', Base.metadata,
    Column('userid', OID),
    Column('dbid', OID),
    Column('toplevel', Boolean),
    Column('queryid', BigInteger),
    Column('query', Text),
    Column('plans', BigInteger),
    Column('total_plan_time', Double(53)),
    Column('min_plan_time', Double(53)),
    Column('max_plan_time', Double(53)),
    Column('mean_plan_time', Double(53)),
    Column('stddev_plan_time', Double(53)),
    Column('calls', BigInteger),
    Column('total_exec_time', Double(53)),
    Column('min_exec_time', Double(53)),
    Column('max_exec_time', Double(53)),
    Column('mean_exec_time', Double(53)),
    Column('stddev_exec_time', Double(53)),
    Column('rows', BigInteger),
    Column('shared_blks_hit', BigInteger),
    Column('shared_blks_read', BigInteger),
    Column('shared_blks_dirtied', BigInteger),
    Column('shared_blks_written', BigInteger),
    Column('local_blks_hit', BigInteger),
    Column('local_blks_read', BigInteger),
    Column('local_blks_dirtied', BigInteger),
    Column('local_blks_written', BigInteger),
    Column('temp_blks_read', BigInteger),
    Column('temp_blks_written', BigInteger),
    Column('blk_read_time', Double(53)),
    Column('blk_write_time', Double(53)),
    Column('temp_blk_read_time', Double(53)),
    Column('temp_blk_write_time', Double(53)),
    Column('wal_records', BigInteger),
    Column('wal_fpi', BigInteger),
    Column('wal_bytes', Numeric),
    Column('jit_functions', BigInteger),
    Column('jit_generation_time', Double(53)),
    Column('jit_inlining_count', BigInteger),
    Column('jit_inlining_time', Double(53)),
    Column('jit_optimization_count', BigInteger),
    Column('jit_optimization_time', Double(53)),
    Column('jit_emission_count', BigInteger),
    Column('jit_emission_time', Double(53))
)


t_pg_stat_statements_info = Table(
    'pg_stat_statements_info', Base.metadata,
    Column('dealloc', BigInteger),
    Column('stats_reset', DateTime(True))
)


class Prosecutor(Base):
    __tablename__ = 'prosecutor'
    __table_args__ = (
        CheckConstraint('experience >= 0', name='prosecutor_experience_check'),
        PrimaryKeyConstraint('prosecutorid', name='prosecutor_pkey')
    )

    prosecutorid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    experience: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[Optional[str]] = mapped_column(String(255))

    cases: Mapped[List['Cases']] = relationship('Cases', secondary='prosecutorassign', back_populates='prosecutor')


class Surety(Base):
    __tablename__ = 'surety'
    __table_args__ = (
        PrimaryKeyConstraint('suretyid', name='surety_pkey'),
    )

    suretyid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cnic: Mapped[str] = mapped_column(String(13))
    phone: Mapped[str] = mapped_column(String(15))
    firstname: Mapped[Optional[str]] = mapped_column(String(255))
    lastname: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    address: Mapped[Optional[str]] = mapped_column(String(255))
    pasthistory: Mapped[Optional[str]] = mapped_column(Text)

    bail: Mapped[List['Bail']] = relationship('Bail', back_populates='surety')


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint("role::text = ANY (ARRAY['Admin'::character varying::text, 'Lawyer'::character varying::text, 'Judge'::character varying::text, 'CourtRegistrar'::character varying::text, 'CaseParticipant'::character varying::text])", name='users_role_check'),
        PrimaryKeyConstraint('userid', name='users_pkey')
    )

    userid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role: Mapped[str] = mapped_column(Enum('Lawyer', 'Judge', 'CaseParticipant', 'CourtRegistrar', 'Admin', name='Role'), server_default=text('\'Admin\'::"Role"'))
    firstname: Mapped[Optional[str]] = mapped_column(String(255))
    lastname: Mapped[Optional[str]] = mapped_column(String(255))
    password: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phoneno: Mapped[Optional[str]] = mapped_column(String(15))
    cnic: Mapped[Optional[str]] = mapped_column(String(15))
    dob: Mapped[Optional[datetime.date]] = mapped_column(Date)
    createdat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    admin: Mapped[List['Admin']] = relationship('Admin', back_populates='users')
    courtregistrar: Mapped[List['Courtregistrar']] = relationship('Courtregistrar', back_populates='users')
    judge: Mapped[List['Judge']] = relationship('Judge', back_populates='users')
    lawyer: Mapped[List['Lawyer']] = relationship('Lawyer', back_populates='users')
    caseparticipant: Mapped[List['Caseparticipant']] = relationship('Caseparticipant', back_populates='users')
    
      
    @property
    def is_active(self):
        # Return True for all users, or add your custom logic here
        return True
    
    @property
    def is_authenticated(self):
        # Return True for all users, or add your custom logic here
        return True
    
    def get_id(self):
        return str(self.userid)
    
    @classmethod
    def from_row(cls, row):
        return cls(
        userid=row[0],
        firstname=row[1],
        lastname=row[2],
        email=row[3],
        phoneno=row[4],
        cnic=row[5],
        dob=row[6],
        password=row[7],
        role=row[8]
    )



class Witnesscase(Base):
    __tablename__ = 'witnesscase'
    __table_args__ = (
        PrimaryKeyConstraint('caseid', 'witnessid', name='witness_casepk'),
    )

    caseid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    witnessid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    statement: Mapped[Optional[str]] = mapped_column(Text)
    statementdate: Mapped[Optional[datetime.date]] = mapped_column(Date)
    createdat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updatedat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class Witnesses(Base):
    __tablename__ = 'witnesses'
    __table_args__ = (
        PrimaryKeyConstraint('witnessid', name='witnesses_pkey'),
    )

    witnessid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    firstname: Mapped[str] = mapped_column(String(255))
    lastname: Mapped[str] = mapped_column(String(255))
    cnic: Mapped[str] = mapped_column(String(13))
    phone: Mapped[Optional[str]] = mapped_column(String(15))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    address: Mapped[Optional[str]] = mapped_column(String(255))
    pasthistory: Mapped[Optional[str]] = mapped_column(Text)


class Admin(Base):
    __tablename__ = 'admin'
    __table_args__ = (
        ForeignKeyConstraint(['userid'], ['users.userid'], ondelete='CASCADE', onupdate='CASCADE', name='adminuserfk'),
        PrimaryKeyConstraint('adminid', name='admin_pkey')
    )

    adminid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    userid: Mapped[Optional[int]] = mapped_column(BigInteger)

    users: Mapped[Optional['Users']] = relationship('Users', back_populates='admin')
    logtable: Mapped[List['Logtable']] = relationship('Logtable', back_populates='admin')


class Appeals(Base):
    __tablename__ = 'appeals'
    __table_args__ = (
        ForeignKeyConstraint(['caseid'], ['cases.caseid'], ondelete='CASCADE', onupdate='CASCADE', name='fk_appeals_case'),
        PrimaryKeyConstraint('caseid', 'appealid', name='appealspk')
    )

    caseid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    appealid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    appealdate: Mapped[datetime.date] = mapped_column(Date)
    appealstatus: Mapped[Optional[str]] = mapped_column(String(100), server_default=text("'forwarded for review'::character varying"))
    decisiondate: Mapped[Optional[datetime.date]] = mapped_column(Date)
    decision: Mapped[Optional[str]] = mapped_column(Text)

    cases: Mapped['Cases'] = relationship('Cases', back_populates='appeals')


class Bail(Base):
    __tablename__ = 'bail'
    __table_args__ = (
        ForeignKeyConstraint(['caseid'], ['cases.caseid'], ondelete='CASCADE', onupdate='CASCADE', name='fk_bail_caseid'),
        ForeignKeyConstraint(['suretyid'], ['surety.suretyid'], ondelete='CASCADE', onupdate='CASCADE', name='fk_bail_suretyid'),
        PrimaryKeyConstraint('caseid', 'bailid', name='bailpk')
    )

    caseid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bailid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    suretyid: Mapped[int] = mapped_column(BigInteger)
    bailstatus: Mapped[Optional[str]] = mapped_column(String(50))
    bailamount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 2))
    baildate: Mapped[Optional[datetime.date]] = mapped_column(Date)
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    bailcondition: Mapped[Optional[str]] = mapped_column(Text)

    cases: Mapped['Cases'] = relationship('Cases', back_populates='bail')
    surety: Mapped['Surety'] = relationship('Surety', back_populates='bail')


class Casehistory(Base):
    __tablename__ = 'casehistory'
    __table_args__ = (
        ForeignKeyConstraint(['caseid'], ['cases.caseid'], ondelete='CASCADE', onupdate='CASCADE', name='fk_casehistory_caseid'),
        PrimaryKeyConstraint('historyid', name='casehistory_pkey')
    )

    historyid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    caseid: Mapped[int] = mapped_column(BigInteger)
    actiondate: Mapped[Optional[datetime.date]] = mapped_column(Date)
    actiontaken: Mapped[Optional[str]] = mapped_column(Text)
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    createdat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updatedat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    cases: Mapped['Cases'] = relationship('Cases', back_populates='casehistory')


t_courtaccess = Table(
    'courtaccess', Base.metadata,
    Column('caseid', BigInteger, primary_key=True, nullable=False),
    Column('courtid', BigInteger, primary_key=True, nullable=False),
    ForeignKeyConstraint(['caseid'], ['cases.caseid'], ondelete='CASCADE', onupdate='CASCADE', name='caseaccessccfk'),
    ForeignKeyConstraint(['courtid'], ['court.courtid'], ondelete='CASCADE', onupdate='CASCADE', name='courtaccessfk'),
    PrimaryKeyConstraint('caseid', 'courtid', name='courtaccesspk')
)


class Courtregistrar(Base):
    __tablename__ = 'courtregistrar'
    __table_args__ = (
        ForeignKeyConstraint(['courtid'], ['court.courtid'], ondelete='CASCADE', onupdate='CASCADE', name='courtcourtregistrarfk'),
        ForeignKeyConstraint(['userid'], ['users.userid'], ondelete='CASCADE', onupdate='CASCADE', name='registraruserfk'),
        PrimaryKeyConstraint('registrarid', name='courtregistrar_pkey')
    )

    registrarid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    userid: Mapped[Optional[int]] = mapped_column(BigInteger)
    courtid: Mapped[Optional[int]] = mapped_column(BigInteger)
    position: Mapped[Optional[str]] = mapped_column(String(255))

    court: Mapped[Optional['Court']] = relationship('Court', back_populates='courtregistrar')
    users: Mapped[Optional['Users']] = relationship('Users', back_populates='courtregistrar')


class Courtroom(Base):
    __tablename__ = 'courtroom'
    __table_args__ = (
        CheckConstraint('capacity >= 0', name='courtroom_capacity_check'),
        ForeignKeyConstraint(['courtid'], ['court.courtid'], ondelete='CASCADE', onupdate='CASCADE', name='courtroomcourtfk'),
        PrimaryKeyConstraint('courtid', 'courtroomid', name='courtroompk')
    )

    courtid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    courtroomid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    courtroomno: Mapped[int] = mapped_column(Integer)
    capacity: Mapped[Optional[int]] = mapped_column(Integer)
    availability: Mapped[Optional[str]] = mapped_column(String)

    court: Mapped['Court'] = relationship('Court', back_populates='courtroom')


class Documentcase(Base):
    __tablename__ = 'documentcase'
    __table_args__ = (
        ForeignKeyConstraint(['caseid'], ['cases.caseid'], ondelete='CASCADE', onupdate='CASCADE', name='fk_documentcase_caseid'),
        ForeignKeyConstraint(['documentid'], ['documents.documentid'], ondelete='CASCADE', onupdate='CASCADE', name='fk_documentcase_documentid'),
        PrimaryKeyConstraint('caseid', 'documentid', name='document_casepk')
    )

    caseid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    documentid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    submissiondate: Mapped[datetime.date] = mapped_column(Date)
    createdat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updatedat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    cases: Mapped['Cases'] = relationship('Cases', back_populates='documentcase')
    documents: Mapped['Documents'] = relationship('Documents', back_populates='documentcase')


class Evidence(Base):
    __tablename__ = 'evidence'
    __table_args__ = (
        ForeignKeyConstraint(['caseid'], ['cases.caseid'], ondelete='CASCADE', onupdate='CASCADE', name='fk_evidence_caseid'),
        PrimaryKeyConstraint('evidenceid', name='evidence_pkey')
    )

    evidenceid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    caseid: Mapped[int] = mapped_column(BigInteger)
    evidencetype: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    submitteddate: Mapped[Optional[datetime.date]] = mapped_column(Date)
    filepath: Mapped[Optional[str]] = mapped_column(String(500))
    createdat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updatedat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    cases: Mapped['Cases'] = relationship('Cases', back_populates='evidence')


class Finaldecision(Base):
    __tablename__ = 'finaldecision'
    __table_args__ = (
        ForeignKeyConstraint(['caseid'], ['cases.caseid'], ondelete='CASCADE', onupdate='CASCADE', name='fk_finaldecision_caseid'),
        PrimaryKeyConstraint('caseid', 'decisionid', name='finaldecisionpk')
    )

    caseid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    decisionid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    decisiondate: Mapped[Optional[datetime.date]] = mapped_column(Date)
    decisionsummary: Mapped[Optional[str]] = mapped_column(Text)
    verdict: Mapped[Optional[str]] = mapped_column(String(255))
    createdat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updatedat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    cases: Mapped['Cases'] = relationship('Cases', back_populates='finaldecision')


class Judge(Base):
    __tablename__ = 'judge'
    __table_args__ = (
        CheckConstraint('expyears >= 0', name='judge_expyears_check'),
        ForeignKeyConstraint(['userid'], ['users.userid'], ondelete='CASCADE', onupdate='CASCADE', name='judgeuserfk'),
        PrimaryKeyConstraint('judgeid', name='judge_pkey')
    )

    judgeid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    userid: Mapped[Optional[int]] = mapped_column(BigInteger)
    position: Mapped[Optional[str]] = mapped_column(String(255))
    appointmentdate: Mapped[Optional[datetime.date]] = mapped_column(Date)
    expyears: Mapped[Optional[int]] = mapped_column(Integer)
    specialization: Mapped[Optional[str]] = mapped_column(String(255))

    cases: Mapped[List['Cases']] = relationship('Cases', secondary='judgeaccess', back_populates='judge')
    court: Mapped[List['Court']] = relationship('Court', secondary='judgeworksin', back_populates='judge')
    users: Mapped[Optional['Users']] = relationship('Users', back_populates='judge')
    hearings: Mapped[List['Hearings']] = relationship('Hearings', back_populates='judge')


class Lawyer(Base):
    __tablename__ = 'lawyer'
    __table_args__ = (
        CheckConstraint('experienceyears >= 0', name='lawyer_experienceyears_check'),
        ForeignKeyConstraint(['userid'], ['users.userid'], ondelete='CASCADE', onupdate='CASCADE', name='lawyeruserfk'),
        PrimaryKeyConstraint('lawyerid', name='lawyer_pkey'),
        UniqueConstraint('barlicenseno', name='lawyer_barlicenseno_key')
    )

    lawyerid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    barlicenseno: Mapped[int] = mapped_column(BigInteger)
    userid: Mapped[Optional[int]] = mapped_column(BigInteger)
    specialization: Mapped[Optional[str]] = mapped_column(String(255))
    experienceyears: Mapped[Optional[int]] = mapped_column(Integer)

    cases: Mapped[List['Cases']] = relationship('Cases', secondary='caselawyeraccess', back_populates='lawyer')
    users: Mapped[Optional['Users']] = relationship('Users', back_populates='lawyer')
    caseparticipant: Mapped[List['Caseparticipant']] = relationship('Caseparticipant', back_populates='lawyer')
    payments: Mapped[List['Payments']] = relationship('Payments', back_populates='lawyer')


t_prosecutorassign = Table(
    'prosecutorassign', Base.metadata,
    Column('prosecutorid', BigInteger, primary_key=True, nullable=False),
    Column('caseid', BigInteger, primary_key=True, nullable=False),
    ForeignKeyConstraint(['caseid'], ['cases.caseid'], name='prosecutorassign_caseid_fkey'),
    ForeignKeyConstraint(['prosecutorid'], ['prosecutor.prosecutorid'], ondelete='CASCADE', onupdate='CASCADE', name='prosecutorassignfk'),
    PrimaryKeyConstraint('prosecutorid', 'caseid', name='prosecutorassignpk')
)


class Remands(Base):
    __tablename__ = 'remands'
    __table_args__ = (
        ForeignKeyConstraint(['caseid'], ['cases.caseid'], ondelete='CASCADE', onupdate='CASCADE', name='fk_remands_case'),
        PrimaryKeyConstraint('caseid', 'remandid', name='remands_pk')
    )

    caseid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    remandid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    startdate: Mapped[datetime.date] = mapped_column(Date)
    enddate: Mapped[datetime.date] = mapped_column(Date)
    remandtype: Mapped[Optional[str]] = mapped_column(String(100))
    remanddate: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    remandreason: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[str]] = mapped_column(String)

    cases: Mapped['Cases'] = relationship('Cases', back_populates='remands')


t_caselawyeraccess = Table(
    'caselawyeraccess', Base.metadata,
    Column('caseid', BigInteger, primary_key=True, nullable=False),
    Column('lawyerid', BigInteger, primary_key=True, nullable=False),
    Column('side', String(20)),
    Column('is_lead', Boolean, default=True),
    ForeignKeyConstraint(['caseid'], ['cases.caseid'], ondelete='CASCADE', onupdate='CASCADE', name='caseaccessfk'),
    ForeignKeyConstraint(['lawyerid'], ['lawyer.lawyerid'], ondelete='CASCADE', onupdate='CASCADE', name='lawyeraccessfk'),
    PrimaryKeyConstraint('caseid', 'lawyerid', name='caselawyeraccesspk')
)


class Caseparticipant(Base):
    __tablename__ = 'caseparticipant'
    __table_args__ = (
        ForeignKeyConstraint(['lawyerid'], ['lawyer.lawyerid'], name='participantlawyerfk'),
        ForeignKeyConstraint(['userid'], ['users.userid'], ondelete='CASCADE', onupdate='CASCADE', name='participantuserfk'),
        PrimaryKeyConstraint('participantid', name='caseparticipant_pkey')
    )

    participantid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    userid: Mapped[Optional[int]] = mapped_column(BigInteger)
    lawyerid: Mapped[Optional[int]] = mapped_column(BigInteger)
    address: Mapped[Optional[str]] = mapped_column(String(255))

    cases: Mapped[List['Cases']] = relationship('Cases', secondary='caseparticipantaccess', back_populates='caseparticipant')
    lawyer: Mapped[Optional['Lawyer']] = relationship('Lawyer', back_populates='caseparticipant')
    users: Mapped[Optional['Users']] = relationship('Users', back_populates='caseparticipant')


class Hearings(Base):
    __tablename__ = 'hearings'
    __table_args__ = (
        ForeignKeyConstraint(['caseid'], ['cases.caseid'], ondelete='CASCADE', onupdate='CASCADE', name='fk_hearings_case'),
        ForeignKeyConstraint(['judgeid'], ['judge.judgeid'], ondelete='CASCADE', onupdate='CASCADE', name='hearings_judgeid_fkey'),
        PrimaryKeyConstraint('caseid', 'hearingid', name='hearingspk'),
        UniqueConstraint('hearingid', name='hearings_hearingid_key')
    )

    caseid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    hearingid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    hearingdate: Mapped[datetime.date] = mapped_column(Date)
    judgeid: Mapped[int] = mapped_column(BigInteger, comment='foreign key to judge (judge who creates hearing)')
    hearingtime: Mapped[Optional[datetime.time]] = mapped_column(Time)
    venue: Mapped[Optional[str]] = mapped_column(String(255))
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    createdat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updatedat: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    
    hearingstatus: Mapped[Optional[str]] = mapped_column(String(50), server_default=text("'scheduled'"))

    cases: Mapped['Cases'] = relationship('Cases', back_populates='hearings')
    judge: Mapped['Judge'] = relationship('Judge', back_populates='hearings')


t_judgeaccess = Table(
    'judgeaccess', Base.metadata,
    Column('caseid', BigInteger, primary_key=True, nullable=False),
    Column('judgeid', BigInteger, primary_key=True, nullable=False),
    ForeignKeyConstraint(['caseid'], ['cases.caseid'], ondelete='CASCADE', onupdate='CASCADE', name='caseaccesscjfk'),
    ForeignKeyConstraint(['judgeid'], ['judge.judgeid'], ondelete='CASCADE', onupdate='CASCADE', name='judgeaccessfk'),
    PrimaryKeyConstraint('caseid', 'judgeid', name='judgeaccesspk')
)


t_judgeworksin = Table(
    'judgeworksin', Base.metadata,
    Column('judgeid', BigInteger, primary_key=True, nullable=False),
    Column('courtid', BigInteger, primary_key=True, nullable=False),
    ForeignKeyConstraint(['courtid'], ['court.courtid'], ondelete='CASCADE', onupdate='CASCADE', name='worksincourtfk'),
    ForeignKeyConstraint(['judgeid'], ['judge.judgeid'], ondelete='CASCADE', onupdate='CASCADE', name='judgeworksinfk'),
    PrimaryKeyConstraint('judgeid', 'courtid', name='judgeworksinpk')
)


class Logtable(Base):
    __tablename__ = 'logtable'
    __table_args__ = (
        ForeignKeyConstraint(['adminid'], ['admin.adminid'], ondelete='SET NULL', onupdate='CASCADE', name='logtableadminfk'),
        PrimaryKeyConstraint('logid', name='logtable_pkey')
    )

    logid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    adminid: Mapped[Optional[int]] = mapped_column(BigInteger)
    actiontype: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[str]] = mapped_column(String(255))
    actiontimestamp: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    entitytype: Mapped[Optional[str]] = mapped_column(String(255))

    admin: Mapped[Optional['Admin']] = relationship('Admin', back_populates='logtable')


class Payments(Base):
    __tablename__ = 'payments'
    __table_args__ = (
        CheckConstraint('balance >= 0::numeric', name='payments_balance_check'),
        CheckConstraint("mode::text = ANY (ARRAY['Cash'::character varying, 'Credit/Debit card'::character varying, 'Online Transfer'::character varying]::text[])", name='payments_mode_check'),
        ForeignKeyConstraint(['caseid'], ['cases.caseid'], ondelete='SET NULL', onupdate='CASCADE', name='paymentcasefk'),
        ForeignKeyConstraint(['courtid'], ['court.courtid'], ondelete='CASCADE', onupdate='CASCADE', name='paymentscourtfk'),
        ForeignKeyConstraint(['lawyerid'], ['lawyer.lawyerid'], ondelete='SET NULL', onupdate='CASCADE', name='paymentslawyerfk'),
        PrimaryKeyConstraint('paymentid', name='payments_pkey')
    )

    paymentid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    mode: Mapped[str] = mapped_column(String(50))
    lawyerid: Mapped[Optional[int]] = mapped_column(BigInteger)
    courtid: Mapped[Optional[int]] = mapped_column(BigInteger)
    caseid: Mapped[Optional[int]] = mapped_column(BigInteger)
    paymenttype: Mapped[Optional[str]] = mapped_column(String(255))
    balance: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 2))
    purpose: Mapped[Optional[str]] = mapped_column(String(255))
    paymentdate: Mapped[Optional[datetime.date]] = mapped_column(Date)
    status: Mapped[Optional[str]] = mapped_column(Enum('Paid', 'Pending', name='payment_status'), server_default=text("'Pending'::payment_status"))

    cases: Mapped[Optional['Cases']] = relationship('Cases', back_populates='payments')
    court: Mapped[Optional['Court']] = relationship('Court', back_populates='payments')
    lawyer: Mapped[Optional['Lawyer']] = relationship('Lawyer', back_populates='payments')


t_caseparticipantaccess = Table(
    'caseparticipantaccess', Base.metadata,
    Column('caseid', BigInteger, primary_key=True, nullable=False),
    Column('participantid', BigInteger, primary_key=True, nullable=False),
    ForeignKeyConstraint(['caseid'], ['cases.caseid'], ondelete='CASCADE', onupdate='CASCADE', name='caseaccesscpfk'),
    ForeignKeyConstraint(['participantid'], ['caseparticipant.participantid'], ondelete='CASCADE', onupdate='CASCADE', name='participantaccessfk'),
    PrimaryKeyConstraint('caseid', 'participantid', name='caseparticipantaccesspk')
)
