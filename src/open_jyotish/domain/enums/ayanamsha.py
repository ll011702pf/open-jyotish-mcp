from enum import StrEnum


class AyanamshaId(StrEnum):
    ALDEBARAN_15TAU = "aldebaran_15tau"
    ARYABHATA = "aryabhata"
    ARYABHATA_522 = "aryabhata_522"
    ARYABHATA_MSUN = "aryabhata_msun"
    B1950 = "b1950"
    BABYL_BRITTON = "babyl_britton"
    BABYL_ETPSC = "babyl_etpsc"
    BABYL_HUBER = "babyl_huber"
    BABYL_KUGLER1 = "babyl_kugler1"
    BABYL_KUGLER2 = "babyl_kugler2"
    BABYL_KUGLER3 = "babyl_kugler3"
    DELUCE = "deluce"
    DJWHAL_KHUL = "djwhal_khul"
    FAGAN_BRADLEY = "fagan_bradley"
    GALALIGN_MARDYKS = "galalign_mardyks"
    GALCENT_0SAG = "galcent_0sag"
    GALCENT_COCHRANE = "galcent_cochrane"
    GALCENT_MULA_WILHELM = "galcent_mula_wilhelm"
    GALCENT_RGILBRAND = "galcent_rgilbrand"
    GALEQU_FIORENZA = "galequ_fiorenza"
    GALEQU_IAU1958 = "galequ_iau1958"
    GALEQU_MULA = "galequ_mula"
    GALEQU_TRUE = "galequ_true"
    HIPPARCHOS = "hipparchos"
    J1900 = "j1900"
    J2000 = "j2000"
    JN_BHASIN = "jn_bhasin"
    LAHIRI = "lahiri"
    LAHIRI_1940 = "lahiri_1940"
    LAHIRI_VP285 = "lahiri_vp285"
    LAHIRI_ICRC = "lahiri_icrc"
    RAMAN = "raman"
    SASSANIAN = "sassanian"
    SS_CITRA = "ss_citra"
    SS_REVATI = "ss_revati"
    KRISHNAMURTI = "krishnamurti"
    KRISHNAMURTI_VP291 = "krishnamurti_vp291"
    YUKTESHWAR = "yukteshwar"
    SURYASIDDHANTA = "suryasiddhanta"
    SURYASIDDHANTA_MSUN = "suryasiddhanta_msun"
    TRUE_CITRA = "true_citra"
    TRUE_MULA = "true_mula"
    TRUE_PUSHYA = "true_pushya"
    TRUE_REVATI = "true_revati"
    TRUE_SHEORAN = "true_sheoran"
    USHASHASHI = "ushashashi"
    VALENS_MOON = "valens_moon"
    CUSTOM = "custom"


AYANAMSHA_LABELS: dict[AyanamshaId, str] = {
    AyanamshaId.ALDEBARAN_15TAU: "Aldebaran 15 Tau",
    AyanamshaId.FAGAN_BRADLEY: "Fagan/Bradley",
    AyanamshaId.LAHIRI: "Lahiri",
    AyanamshaId.LAHIRI_1940: "Lahiri 1940",
    AyanamshaId.LAHIRI_VP285: "Lahiri VP285",
    AyanamshaId.LAHIRI_ICRC: "Lahiri ICRC",
    AyanamshaId.DELUCE: "De Luce",
    AyanamshaId.RAMAN: "Raman",
    AyanamshaId.USHASHASHI: "Ushashashi",
    AyanamshaId.KRISHNAMURTI: "Krishnamurti",
    AyanamshaId.KRISHNAMURTI_VP291: "Krishnamurti VP291",
    AyanamshaId.DJWHAL_KHUL: "Djwhal Khul",
    AyanamshaId.YUKTESHWAR: "Yukteshwar",
    AyanamshaId.JN_BHASIN: "JN Bhasin",
    AyanamshaId.BABYL_KUGLER1: "Babyl Kugler 1",
    AyanamshaId.BABYL_KUGLER2: "Babyl Kugler 2",
    AyanamshaId.BABYL_KUGLER3: "Babyl Kugler 3",
    AyanamshaId.BABYL_HUBER: "Babyl Huber",
    AyanamshaId.BABYL_ETPSC: "Babyl ETPSC",
    AyanamshaId.HIPPARCHOS: "Hipparchos",
    AyanamshaId.SASSANIAN: "Sassanian",
    AyanamshaId.GALCENT_0SAG: "Galcent 0 Sag",
    AyanamshaId.J2000: "J2000",
    AyanamshaId.J1900: "J1900",
    AyanamshaId.B1950: "B1950",
    AyanamshaId.SURYASIDDHANTA: "Surya Siddhanta",
    AyanamshaId.SURYASIDDHANTA_MSUN: "Surya Siddhanta MSun",
    AyanamshaId.ARYABHATA: "Aryabhata",
    AyanamshaId.ARYABHATA_MSUN: "Aryabhata MSun",
    AyanamshaId.SS_REVATI: "SS Revati",
    AyanamshaId.SS_CITRA: "SS Citra",
    AyanamshaId.TRUE_CITRA: "True Citra",
    AyanamshaId.TRUE_REVATI: "True Revati",
    AyanamshaId.TRUE_PUSHYA: "True Pushya",
    AyanamshaId.GALCENT_RGILBRAND: "Galcent Rgilbrand",
    AyanamshaId.GALEQU_IAU1958: "Galequ IAU 1958",
    AyanamshaId.GALEQU_TRUE: "Galequ True",
    AyanamshaId.GALEQU_MULA: "Galequ Mula",
    AyanamshaId.GALALIGN_MARDYKS: "Galalign Mardyks",
    AyanamshaId.TRUE_MULA: "True Mula",
    AyanamshaId.GALCENT_MULA_WILHELM: "Galcent Mula Wilhelm",
    AyanamshaId.ARYABHATA_522: "Aryabhata 522",
    AyanamshaId.BABYL_BRITTON: "Babyl Britton",
    AyanamshaId.TRUE_SHEORAN: "True Sheoran",
    AyanamshaId.GALCENT_COCHRANE: "Galcent Cochrane",
    AyanamshaId.GALEQU_FIORENZA: "Galequ Fiorenza",
    AyanamshaId.VALENS_MOON: "Valens Moon",
    AyanamshaId.CUSTOM: "Custom",
}

AYANAMSHA_OPTIONS: tuple[AyanamshaId, ...] = (
    AyanamshaId.ALDEBARAN_15TAU,
    AyanamshaId.LAHIRI,
    AyanamshaId.LAHIRI_1940,
    AyanamshaId.LAHIRI_VP285,
    AyanamshaId.LAHIRI_ICRC,
    AyanamshaId.DELUCE,
    AyanamshaId.RAMAN,
    AyanamshaId.USHASHASHI,
    AyanamshaId.KRISHNAMURTI,
    AyanamshaId.KRISHNAMURTI_VP291,
    AyanamshaId.DJWHAL_KHUL,
    AyanamshaId.YUKTESHWAR,
    AyanamshaId.JN_BHASIN,
    AyanamshaId.BABYL_KUGLER1,
    AyanamshaId.BABYL_KUGLER2,
    AyanamshaId.BABYL_KUGLER3,
    AyanamshaId.BABYL_HUBER,
    AyanamshaId.BABYL_ETPSC,
    AyanamshaId.FAGAN_BRADLEY,
    AyanamshaId.HIPPARCHOS,
    AyanamshaId.SASSANIAN,
    AyanamshaId.GALCENT_0SAG,
    AyanamshaId.J2000,
    AyanamshaId.J1900,
    AyanamshaId.B1950,
    AyanamshaId.SURYASIDDHANTA,
    AyanamshaId.SURYASIDDHANTA_MSUN,
    AyanamshaId.ARYABHATA,
    AyanamshaId.ARYABHATA_MSUN,
    AyanamshaId.SS_REVATI,
    AyanamshaId.SS_CITRA,
    AyanamshaId.TRUE_CITRA,
    AyanamshaId.TRUE_PUSHYA,
    AyanamshaId.TRUE_REVATI,
    AyanamshaId.GALCENT_RGILBRAND,
    AyanamshaId.GALEQU_IAU1958,
    AyanamshaId.GALEQU_TRUE,
    AyanamshaId.GALEQU_MULA,
    AyanamshaId.GALALIGN_MARDYKS,
    AyanamshaId.TRUE_MULA,
    AyanamshaId.GALCENT_MULA_WILHELM,
    AyanamshaId.ARYABHATA_522,
    AyanamshaId.BABYL_BRITTON,
    AyanamshaId.TRUE_SHEORAN,
    AyanamshaId.GALCENT_COCHRANE,
    AyanamshaId.GALEQU_FIORENZA,
    AyanamshaId.VALENS_MOON,
    AyanamshaId.CUSTOM,
)
