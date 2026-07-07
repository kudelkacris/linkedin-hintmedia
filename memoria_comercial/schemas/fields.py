"""
fields.py — Enumeraciones y valores válidos del schema de conversación.
Fuente de verdad para normalización. Sin lógica de negocio.
Agregar valores nuevos aquí cuando aparezcan sectores o tipos nuevos.
"""
from enum import Enum


class Sector(str, Enum):
    ENERGIA_INFRA       = "ENERGIA_INFRA"        # TGS, Transener, oil & gas, utilities
    SEGUROS_FINANZAS    = "SEGUROS_FINANZAS"      # Libra Seguros, bancos, fintech
    RETAIL_MODA         = "RETAIL_MODA"           # Destiny Group, Tasarolli, ecommerce
    CONSULTORIA_TECH    = "CONSULTORIA_TECH"      # agencias, consultoras, SaaS
    FARMACEUTICO_SALUD  = "FARMACEUTICO_SALUD"    # laboratorios, clínicas, distribución pharma
    TURISMO_EVENTOS     = "TURISMO_EVENTOS"       # hoteles, agencias de viaje, eventos
    MINERIA             = "MINERIA"               # Ingenalse, T&G, extracción
    CONSTRUCCION        = "CONSTRUCCION"          # real estate, desarrolladoras, infraestructura
    MARKETING_BRANDING  = "MARKETING_BRANDING"   # agencias creativas, diseño, comunicación
    EDUCACION           = "EDUCACION"             # universidades, edtech, capacitación
    LOGISTICA           = "LOGISTICA"             # transporte, cadena de suministro
    ALIMENTACION        = "ALIMENTACION"          # alimentos, bebidas, FMCG
    TELECOMUNICACIONES  = "TELECOMUNICACIONES"    # telcos, ISPs
    MANUFACTURA         = "MANUFACTURA"           # industria, producción, productos físicos
    AGRO                = "AGRO"                  # agropecuario, agroindustria
    GOBIERNO            = "GOBIERNO"              # sector público, ONGs, organismos
    BELLEZA_LUJO        = "BELLEZA_LUJO"          # cosméticos, perfumería, moda premium
    AMAZON_ECOMMERCE    = "AMAZON_ECOMMERCE"      # Walmart Connect, Amazon Ads, marketplaces
    OTROS               = "OTROS"
    DESCONOCIDO         = "DESCONOCIDO"


class Seniority(str, Enum):
    CEO         = "CEO"         # CEO, Fundador, Presidente, Dueño
    VP          = "VP"          # VP, Vice President, SVP
    DIRECTOR    = "DIRECTOR"    # Director, Head of
    MANAGER     = "MANAGER"     # Gerente, Manager, Jefe de
    SPECIALIST  = "SPECIALIST"  # Especialista, Analista, Coordinador
    OTHER       = "OTHER"       # cargos no clasificables
    DESCONOCIDO = "DESCONOCIDO"


class TipoDecisor(str, Enum):
    DECISION_MAKER  = "DECISION_MAKER"   # quien decide la contratación
    INFLUENCER      = "INFLUENCER"       # influye pero no decide solo
    SPECIALIST      = "SPECIALIST"       # ejecuta, no decide
    PARTNER         = "PARTNER"          # colaboración, no venta directa
    DESCONOCIDO     = "DESCONOCIDO"


class ResultadoFinal(str, Enum):
    CLIENTE              = "CLIENTE"             # contrató Hint Media
    REUNION              = "REUNION"             # reunión agendada (stage 6)
    DOSSIER              = "DOSSIER"             # dossier enviado, sin avance posterior
    EN_PROCESO           = "EN_PROCESO"          # conversación activa, sin resultado final
    SIN_RESPUESTA        = "SIN_RESPUESTA"       # nunca respondió
    CERRADO_NEGATIVO     = "CERRADO_NEGATIVO"    # cerrado por objeción explícita
    CERRADO_SIN_INTERES  = "CERRADO_SIN_INTERES" # cerrado porque no hay fit


class ObjecionPrincipal(str, Enum):
    HAS_AGENCY      = "HAS_AGENCY"       # ya tienen agencia
    NO_BUDGET       = "NO_BUDGET"        # sin presupuesto
    BAD_TIMING      = "BAD_TIMING"       # mal momento
    PARTNERSHIP     = "PARTNERSHIP"      # querían colaborar, no contratar
    CURIOSITY_ONLY  = "CURIOSITY_ONLY"   # solo curiosidad, sin intención real
    INTERNAL_TEAM   = "INTERNAL_TEAM"    # equipo interno (caso Sarah Valencia)
    NONE            = "NONE"             # sin objeción detectada
    DESCONOCIDA     = "DESCONOCIDA"


class EngagementLevel(str, Enum):
    HIGH        = "HIGH"        # respuestas largas, preguntas, entusiasmo
    MEDIUM      = "MEDIUM"      # respuestas cortas pero positivas
    LOW         = "LOW"         # respuestas mínimas o frías
    DESCONOCIDO = "DESCONOCIDO" # no respondió o no clasificable


class VarianteMsg1(str, Enum):
    A           = "A"           # señal humana: persona, publicación, reflexión
    C           = "C"           # trabajo: logro profesional, resultado concreto
    DESCONOCIDA = "DESCONOCIDA"


class Stage(int, Enum):
    MSG1_ENVIADO        = 1
    MSG2_ENVIADO        = 2
    DOSSIER_ENVIADO     = 3
    SEG1_ENVIADO        = 4
    SEG2_ENVIADO        = 5
    REUNION_AGENDADA    = 6
