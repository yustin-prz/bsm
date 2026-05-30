# ── Command catalog ─────────────────────────────────────────────────────────────
# (id, etiqueta en español). El usuario puede escribir cualquier id manualmente.
ITEMS = [
    ("minecraft:diamond", "Diamante"),
    ("minecraft:diamond_block", "Bloque de diamante"),
    ("minecraft:diamond_sword", "Espada de diamante"),
    ("minecraft:diamond_pickaxe", "Pico de diamante"),
    ("minecraft:diamond_axe", "Hacha de diamante"),
    ("minecraft:diamond_shovel", "Pala de diamante"),
    ("minecraft:diamond_helmet", "Casco de diamante"),
    ("minecraft:diamond_chestplate", "Peto de diamante"),
    ("minecraft:diamond_leggings", "Grebas de diamante"),
    ("minecraft:diamond_boots", "Botas de diamante"),
    ("minecraft:netherite_ingot", "Lingote de netherita"),
    ("minecraft:netherite_sword", "Espada de netherita"),
    ("minecraft:netherite_pickaxe", "Pico de netherita"),
    ("minecraft:netherite_axe", "Hacha de netherita"),
    ("minecraft:iron_ingot", "Lingote de hierro"),
    ("minecraft:iron_block", "Bloque de hierro"),
    ("minecraft:iron_sword", "Espada de hierro"),
    ("minecraft:iron_pickaxe", "Pico de hierro"),
    ("minecraft:gold_ingot", "Lingote de oro"),
    ("minecraft:gold_block", "Bloque de oro"),
    ("minecraft:golden_apple", "Manzana dorada"),
    ("minecraft:enchanted_golden_apple", "Manzana dorada encantada"),
    ("minecraft:emerald", "Esmeralda"),
    ("minecraft:coal", "Carbón"),
    ("minecraft:charcoal", "Carbón vegetal"),
    ("minecraft:redstone", "Polvo de redstone"),
    ("minecraft:redstone_block", "Bloque de redstone"),
    ("minecraft:lapis_lazuli", "Lapislázuli"),
    ("minecraft:quartz", "Cuarzo del Nether"),
    ("minecraft:stick", "Palo"),
    ("minecraft:torch", "Antorcha"),
    ("minecraft:lantern", "Linterna"),
    ("minecraft:crafting_table", "Mesa de trabajo"),
    ("minecraft:furnace", "Horno"),
    ("minecraft:chest", "Cofre"),
    ("minecraft:ender_chest", "Cofre de Ender"),
    ("minecraft:shulker_box", "Caja de shulker"),
    ("minecraft:barrel", "Barril"),
    ("minecraft:hopper", "Tolva"),
    ("minecraft:dispenser", "Dispensador"),
    ("minecraft:dropper", "Soltador"),
    ("minecraft:observer", "Observador"),
    ("minecraft:piston", "Pistón"),
    ("minecraft:sticky_piston", "Pistón pegajoso"),
    ("minecraft:lever", "Palanca"),
    ("minecraft:bucket", "Cubo"),
    ("minecraft:water_bucket", "Cubo de agua"),
    ("minecraft:lava_bucket", "Cubo de lava"),
    ("minecraft:milk_bucket", "Cubo de leche"),
    ("minecraft:bread", "Pan"),
    ("minecraft:apple", "Manzana"),
    ("minecraft:cooked_beef", "Filete"),
    ("minecraft:cooked_chicken", "Pollo cocido"),
    ("minecraft:cooked_porkchop", "Cerdo cocido"),
    ("minecraft:carrot", "Zanahoria"),
    ("minecraft:potato", "Patata"),
    ("minecraft:wheat", "Trigo"),
    ("minecraft:sugar_cane", "Caña de azúcar"),
    ("minecraft:cake", "Pastel"),
    ("minecraft:bow", "Arco"),
    ("minecraft:arrow", "Flecha"),
    ("minecraft:crossbow", "Ballesta"),
    ("minecraft:trident", "Tridente"),
    ("minecraft:shield", "Escudo"),
    ("minecraft:totem_of_undying", "Tótem de la inmortalidad"),
    ("minecraft:elytra", "Élitros"),
    ("minecraft:fishing_rod", "Caña de pescar"),
    ("minecraft:flint_and_steel", "Mechero"),
    ("minecraft:shears", "Tijeras"),
    ("minecraft:tnt", "TNT"),
    ("minecraft:obsidian", "Obsidiana"),
    ("minecraft:cobblestone", "Roca"),
    ("minecraft:stone", "Piedra"),
    ("minecraft:dirt", "Tierra"),
    ("minecraft:grass_block", "Bloque de hierba"),
    ("minecraft:sand", "Arena"),
    ("minecraft:gravel", "Grava"),
    ("minecraft:oak_log", "Tronco de roble"),
    ("minecraft:oak_planks", "Tablas de roble"),
    ("minecraft:glass", "Vidrio"),
    ("minecraft:glowstone", "Piedra luminosa"),
    ("minecraft:sea_lantern", "Linterna marina"),
    ("minecraft:bookshelf", "Estantería"),
    ("minecraft:book", "Libro"),
    ("minecraft:enchanted_book", "Libro encantado"),
    ("minecraft:experience_bottle", "Botella de experiencia"),
    ("minecraft:ender_pearl", "Perla de Ender"),
    ("minecraft:ender_eye", "Ojo de Ender"),
    ("minecraft:blaze_rod", "Vara de blaze"),
    ("minecraft:blaze_powder", "Polvo de blaze"),
    ("minecraft:nether_star", "Estrella del Nether"),
    ("minecraft:beacon", "Faro"),
    ("minecraft:anvil", "Yunque"),
    ("minecraft:enchanting_table", "Mesa de encantamientos"),
    ("minecraft:brewing_stand", "Soporte para pociones"),
    ("minecraft:cauldron", "Caldero"),
    ("minecraft:bed", "Cama"),
    ("minecraft:saddle", "Montura"),
    ("minecraft:name_tag", "Etiqueta"),
    ("minecraft:lead", "Correa"),
    ("minecraft:compass", "Brújula"),
    ("minecraft:clock", "Reloj"),
    ("minecraft:map", "Mapa vacío"),
    ("minecraft:spyglass", "Catalejo"),
    ("minecraft:bone", "Hueso"),
    ("minecraft:string", "Cuerda"),
    ("minecraft:gunpowder", "Pólvora"),
    ("minecraft:slime_ball", "Bola de slime"),
    ("minecraft:leather", "Cuero"),
    ("minecraft:feather", "Pluma"),
    ("minecraft:egg", "Huevo"),
    ("minecraft:potion", "Poción"),
    ("minecraft:splash_potion", "Poción arrojadiza"),
    ("minecraft:glass_bottle", "Botella de vidrio"),
    ("minecraft:firework_rocket", "Cohete de fuegos artificiales"),
    ("minecraft:minecart", "Vagoneta"),
    ("minecraft:campfire", "Hoguera"),
]

# Efectos para /effect (nombres cortos que acepta Bedrock)
EFFECTS = [
    ("speed", "Velocidad"), ("slowness", "Lentitud"), ("haste", "Prisa"),
    ("mining_fatigue", "Fatiga minera"), ("strength", "Fuerza"),
    ("instant_health", "Salud instantánea"), ("instant_damage", "Daño instantáneo"),
    ("jump_boost", "Salto"), ("nausea", "Náusea"), ("regeneration", "Regeneración"),
    ("resistance", "Resistencia"), ("fire_resistance", "Resistencia al fuego"),
    ("water_breathing", "Respiración acuática"), ("invisibility", "Invisibilidad"),
    ("blindness", "Ceguera"), ("night_vision", "Visión nocturna"),
    ("hunger", "Hambre"), ("weakness", "Debilidad"), ("poison", "Veneno"),
    ("wither", "Marchitamiento"), ("health_boost", "Vida extra"),
    ("absorption", "Absorción"), ("saturation", "Saturación"),
    ("levitation", "Levitación"), ("slow_falling", "Caída lenta"),
    ("conduit_power", "Poder del conducto"), ("village_hero", "Héroe de la aldea"),
    ("darkness", "Oscuridad"),
]

# Encantamientos para /enchant
ENCHANTS = [
    ("protection", "Protección"), ("fire_protection", "Protección contra fuego"),
    ("feather_falling", "Caída de pluma"), ("blast_protection", "Protección contra explosiones"),
    ("projectile_protection", "Protección contra proyectiles"), ("thorns", "Espinas"),
    ("respiration", "Respiración"), ("depth_strider", "Agilidad acuática"),
    ("aqua_affinity", "Afinidad acuática"), ("sharpness", "Filo"),
    ("smite", "Castigo"), ("bane_of_arthropods", "Perdición de los artrópodos"),
    ("knockback", "Empuje"), ("fire_aspect", "Aspecto ígneo"), ("looting", "Botín"),
    ("efficiency", "Eficiencia"), ("silk_touch", "Toque de seda"),
    ("unbreaking", "Irrompibilidad"), ("fortune", "Fortuna"), ("power", "Poder"),
    ("punch", "Retroceso"), ("flame", "Fuego"), ("infinity", "Infinidad"),
    ("luck_of_the_sea", "Suerte marina"), ("lure", "Atracción"),
    ("frost_walker", "Paso helado"), ("mending", "Reparación"),
    ("vanishing", "Maldición de desaparición"), ("binding", "Maldición de vinculación"),
    ("impaling", "Empalamiento"), ("riptide", "Estela"), ("loyalty", "Lealtad"),
    ("channeling", "Canalización"), ("multishot", "Multidisparo"),
    ("piercing", "Perforación"), ("quick_charge", "Carga rápida"),
    ("soul_speed", "Velocidad de almas"), ("swift_sneak", "Sigilo veloz"),
]

ENTITIES = [
    ("minecraft:zombie", "Zombi"), ("minecraft:skeleton", "Esqueleto"),
    ("minecraft:creeper", "Creeper"), ("minecraft:spider", "Araña"),
    ("minecraft:enderman", "Enderman"), ("minecraft:cow", "Vaca"),
    ("minecraft:pig", "Cerdo"), ("minecraft:sheep", "Oveja"),
    ("minecraft:chicken", "Gallina"), ("minecraft:horse", "Caballo"),
    ("minecraft:wolf", "Lobo"), ("minecraft:cat", "Gato"),
    ("minecraft:villager", "Aldeano"), ("minecraft:iron_golem", "Gólem de hierro"),
    ("minecraft:ender_dragon", "Dragón del End"), ("minecraft:wither", "Wither"),
    ("minecraft:allay", "Allay"), ("minecraft:axolotl", "Ajolote"),
    ("minecraft:fox", "Zorro"), ("minecraft:bee", "Abeja"),
]

GAMEMODES = [("survival", "Supervivencia"), ("creative", "Creativo"),
             ("adventure", "Aventura"), ("spectator", "Espectador")]
DIFFICULTIES = [("peaceful", "Pacífico"), ("easy", "Fácil"),
                ("normal", "Normal"), ("hard", "Difícil")]
WEATHERS = [("clear", "Despejado"), ("rain", "Lluvia"), ("thunder", "Tormenta")]
TIME_PRESETS = [("day", "Día"), ("noon", "Mediodía"), ("night", "Noche"),
                ("midnight", "Medianoche"), ("sunrise", "Amanecer"), ("sunset", "Atardecer")]
GAMERULES = [
    ("keepInventory", "Conservar inventario"), ("doDaylightCycle", "Ciclo día/noche"),
    ("doWeatherCycle", "Ciclo de clima"), ("doMobSpawning", "Generación de mobs"),
    ("mobGriefing", "Mobs alteran bloques"), ("doFireTick", "Propagación de fuego"),
    ("pvp", "PvP"), ("showCoordinates", "Mostrar coordenadas"),
    ("randomTickSpeed", "Velocidad de tick aleatorio"), ("doImmediateRespawn", "Reaparición inmediata"),
    ("fallDamage", "Daño por caída"), ("fireDamage", "Daño por fuego"),
    ("naturalRegeneration", "Regeneración natural"), ("tntExplodes", "TNT explota"),
    ("commandBlockOutput", "Salida de bloques de comandos"),
    ("sendCommandFeedback", "Retroalimentación de comandos"),
]

# Selectores de objetivo de Minecraft
TARGET_SELECTORS = ["@a", "@p", "@r", "@s", "@e"]


class Param:
    def __init__(self, key, label, kind, options=None, default="", optional=False, placeholder=""):
        self.key = key
        self.label = label
        self.kind = kind          # player | item | effect | enchant | entity | int | text | enum | bool
        self.options = options or []
        self.default = default
        self.optional = optional
        self.placeholder = placeholder


class CommandSpec:
    def __init__(self, key, label, name, params, build=None, hint=""):
        self.key = key
        self.label = label        # shown in the command searcher
        self.name = name          # command prefix, e.g. "give" or "time set"
        self.params = params
        self.build = build        # optional custom builder: fn(tab) -> (cmd|None, err|None)
        self.hint = hint


# Custom builders ----------------------------------------------------------------
def _build_xp(tab):
    amount = tab.val("amount")
    player = tab.val("player")
    if not amount:
        return None, "Falta la cantidad de experiencia."
    if not player:
        return None, "Falta el jugador."
    suffix = "L" if tab.checked("levels") else ""
    return f"xp {amount}{suffix} {player}", None


def _build_effect_clear(tab):
    player = tab.val("player")
    if not player:
        return None, "Falta el jugador."
    return f"effect {player} clear", None


COMMANDS = [
    CommandSpec("give", "Dar objeto (give)", "give", [
        Param("player", "Jugador", "player"),
        Param("item", "Objeto", "item"),
        Param("amount", "Cantidad", "int", default="1", optional=True),
    ], hint="give <jugador> <objeto> [cantidad]"),
    CommandSpec("kick", "Expulsar jugador (kick)", "kick", [
        Param("player", "Jugador", "player"),
        Param("reason", "Motivo", "text", optional=True, placeholder="Opcional"),
    ], hint="kick <jugador> [motivo]"),
    CommandSpec("kill", "Eliminar (kill)", "kill", [
        Param("target", "Objetivo", "player"),
    ], hint="kill <objetivo>"),
    CommandSpec("gamemode", "Modo de juego (gamemode)", "gamemode", [
        Param("mode", "Modo", "enum", options=GAMEMODES),
        Param("player", "Jugador", "player"),
    ], hint="gamemode <modo> <jugador>"),
    CommandSpec("tp", "Teletransportar (tp)", "tp", [
        Param("player", "Jugador a mover", "player"),
        Param("destination", "Destino (jugador)", "player"),
    ], hint="tp <jugador> <destino>"),
    CommandSpec("teleport_coords", "Teletransportar a coords (tp)", "tp", [
        Param("player", "Jugador", "player"),
        Param("coords", "Coordenadas X Y Z", "text", placeholder="100 64 -200"),
    ], hint="tp <jugador> <x y z>"),
    CommandSpec("effect_give", "Dar efecto (effect)", "effect", [
        Param("player", "Jugador", "player"),
        Param("effect", "Efecto", "effect"),
        Param("seconds", "Segundos", "int", default="30", optional=True),
        Param("amplifier", "Nivel (amplificador)", "int", default="0", optional=True),
    ], hint="effect <jugador> <efecto> [segundos] [nivel]"),
    CommandSpec("effect_clear", "Quitar efectos (effect clear)", "effect",
                [Param("player", "Jugador", "player")],
                build=_build_effect_clear, hint="effect <jugador> clear"),
    CommandSpec("enchant", "Encantar objeto en mano (enchant)", "enchant", [
        Param("player", "Jugador", "player"),
        Param("enchant", "Encantamiento", "enchant"),
        Param("level", "Nivel", "int", default="1", optional=True),
    ], hint="enchant <jugador> <encantamiento> [nivel]"),
    CommandSpec("xp", "Dar experiencia (xp)", "xp", [
        Param("amount", "Cantidad", "int", default="100"),
        Param("levels", "En niveles (no en puntos)", "bool"),
        Param("player", "Jugador", "player"),
    ], build=_build_xp, hint="xp <cantidad>[L] <jugador>"),
    CommandSpec("clear", "Vaciar inventario (clear)", "clear", [
        Param("player", "Jugador", "player"),
        Param("item", "Objeto (opcional)", "item", optional=True),
        Param("maxCount", "Cantidad máx.", "int", optional=True),
    ], hint="clear <jugador> [objeto] [cantidad]"),
    CommandSpec("summon", "Invocar entidad (summon)", "summon", [
        Param("entity", "Entidad", "entity"),
        Param("coords", "Coordenadas X Y Z", "text", optional=True, placeholder="Opcional"),
    ], hint="summon <entidad> [x y z]"),
    CommandSpec("time", "Cambiar hora (time set)", "time set", [
        Param("value", "Hora", "enum", options=TIME_PRESETS),
    ], hint="time set <valor>"),
    CommandSpec("weather", "Cambiar clima (weather)", "weather", [
        Param("type", "Clima", "enum", options=WEATHERS),
        Param("duration", "Duración (s)", "int", optional=True),
    ], hint="weather <tipo> [duración]"),
    CommandSpec("difficulty", "Dificultad (difficulty)", "difficulty", [
        Param("level", "Dificultad", "enum", options=DIFFICULTIES),
    ], hint="difficulty <nivel>"),
    CommandSpec("gamerule", "Regla de juego (gamerule)", "gamerule", [
        Param("rule", "Regla", "enum", options=GAMERULES),
        Param("value", "Valor", "text", default="true", placeholder="true / false / número"),
    ], hint="gamerule <regla> <valor>"),
    CommandSpec("say", "Mensaje global (say)", "say", [
        Param("message", "Mensaje", "text", placeholder="Texto a mostrar a todos"),
    ], hint="say <mensaje>"),
    CommandSpec("tell", "Mensaje privado (tell)", "tell", [
        Param("player", "Jugador", "player"),
        Param("message", "Mensaje", "text"),
    ], hint="tell <jugador> <mensaje>"),
    CommandSpec("list", "Listar jugadores (list)", "list", [], hint="list"),
    CommandSpec("op", "Dar operador (op)", "op", [
        Param("player", "Jugador", "player"),
    ], hint="op <jugador>"),
    CommandSpec("deop", "Quitar operador (deop)", "deop", [
        Param("player", "Jugador", "player"),
    ], hint="deop <jugador>"),
    CommandSpec("changesetting", "Cambiar ajuste en vivo (changesetting)", "changesetting", [
        Param("setting", "Ajuste", "enum",
              options=[("allow-cheats", "allow-cheats"), ("difficulty", "difficulty")]),
        Param("value", "Valor", "text", placeholder="true/false  ·  peaceful/easy/normal/hard"),
    ], hint="changesetting <allow-cheats|difficulty> <valor>"),
]
COMMANDS_BY_KEY = {c.key: c for c in COMMANDS}
