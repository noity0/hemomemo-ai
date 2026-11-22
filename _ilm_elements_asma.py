# -*- coding: utf-8 -*-
"""_ilm_elements_asma.py — 118 elements (naam|symbol|number|category) + Asma-ul-Husna (naam|ma'ni)."""

_ELEMENTS = """\
Hydrogen|H|1|Nonmetal
Helium|He|2|Noble gas
Lithium|Li|3|Alkali metal
Beryllium|Be|4|Alkaline earth metal
Boron|B|5|Metalloid
Carbon|C|6|Nonmetal
Nitrogen|N|7|Nonmetal
Oxygen|O|8|Nonmetal
Fluorine|F|9|Halogen
Neon|Ne|10|Noble gas
Sodium|Na|11|Alkali metal
Magnesium|Mg|12|Alkaline earth metal
Aluminium|Al|13|Post-transition metal
Silicon|Si|14|Metalloid
Phosphorus|P|15|Nonmetal
Sulfur|S|16|Nonmetal
Chlorine|Cl|17|Halogen
Argon|Ar|18|Noble gas
Potassium|K|19|Alkali metal
Calcium|Ca|20|Alkaline earth metal
Scandium|Sc|21|Transition metal
Titanium|Ti|22|Transition metal
Vanadium|V|23|Transition metal
Chromium|Cr|24|Transition metal
Manganese|Mn|25|Transition metal
Iron|Fe|26|Transition metal
Cobalt|Co|27|Transition metal
Nickel|Ni|28|Transition metal
Copper|Cu|29|Transition metal
Zinc|Zn|30|Transition metal
Gallium|Ga|31|Post-transition metal
Germanium|Ge|32|Metalloid
Arsenic|As|33|Metalloid
Selenium|Se|34|Nonmetal
Bromine|Br|35|Halogen
Krypton|Kr|36|Noble gas
Rubidium|Rb|37|Alkali metal
Strontium|Sr|38|Alkaline earth metal
Yttrium|Y|39|Transition metal
Zirconium|Zr|40|Transition metal
Niobium|Nb|41|Transition metal
Molybdenum|Mo|42|Transition metal
Technetium|Tc|43|Transition metal
Ruthenium|Ru|44|Transition metal
Rhodium|Rh|45|Transition metal
Palladium|Pd|46|Transition metal
Silver|Ag|47|Transition metal
Cadmium|Cd|48|Transition metal
Indium|In|49|Post-transition metal
Tin|Sn|50|Post-transition metal
Antimony|Sb|51|Metalloid
Tellurium|Te|52|Metalloid
Iodine|I|53|Halogen
Xenon|Xe|54|Noble gas
Caesium|Cs|55|Alkali metal
Barium|Ba|56|Alkaline earth metal
Lanthanum|La|57|Lanthanide
Cerium|Ce|58|Lanthanide
Praseodymium|Pr|59|Lanthanide
Neodymium|Nd|60|Lanthanide
Promethium|Pm|61|Lanthanide
Samarium|Sm|62|Lanthanide
Europium|Eu|63|Lanthanide
Gadolinium|Gd|64|Lanthanide
Terbium|Tb|65|Lanthanide
Dysprosium|Dy|66|Lanthanide
Holmium|Ho|67|Lanthanide
Erbium|Er|68|Lanthanide
Thulium|Tm|69|Lanthanide
Ytterbium|Yb|70|Lanthanide
Lutetium|Lu|71|Lanthanide
Hafnium|Hf|72|Transition metal
Tantalum|Ta|73|Transition metal
Tungsten|W|74|Transition metal
Rhenium|Re|75|Transition metal
Osmium|Os|76|Transition metal
Iridium|Ir|77|Transition metal
Platinum|Pt|78|Transition metal
Gold|Au|79|Transition metal
Mercury|Hg|80|Transition metal
Thallium|Tl|81|Post-transition metal
Lead|Pb|82|Post-transition metal
Bismuth|Bi|83|Post-transition metal
Polonium|Po|84|Metalloid
Astatine|At|85|Halogen
Radon|Rn|86|Noble gas
Francium|Fr|87|Alkali metal
Radium|Ra|88|Alkaline earth metal
Actinium|Ac|89|Actinide
Thorium|Th|90|Actinide
Protactinium|Pa|91|Actinide
Uranium|U|92|Actinide
Neptunium|Np|93|Actinide
Plutonium|Pu|94|Actinide
Americium|Am|95|Actinide
Curium|Cm|96|Actinide
Berkelium|Bk|97|Actinide
Californium|Cf|98|Actinide
Einsteinium|Es|99|Actinide
Fermium|Fm|100|Actinide
Mendelevium|Md|101|Actinide
Nobelium|No|102|Actinide
Lawrencium|Lr|103|Actinide
Rutherfordium|Rf|104|Transition metal
Dubnium|Db|105|Transition metal
Seaborgium|Sg|106|Transition metal
Bohrium|Bh|107|Transition metal
Hassium|Hs|108|Transition metal
Meitnerium|Mt|109|Unknown
Darmstadtium|Ds|110|Unknown
Roentgenium|Rg|111|Unknown
Copernicium|Cn|112|Unknown
Nihonium|Nh|113|Unknown
Flerovium|Fl|114|Unknown
Moscovium|Mc|115|Unknown
Livermorium|Lv|116|Unknown
Tennessine|Ts|117|Unknown
Oganesson|Og|118|Unknown"""

# Asma-ul-Husna (naam|ma'ni) — 99. Sirf naam+ma'ni (order-number ka daawa nahi,
# imandari-sach: tarteef me ikhtilaf hai, isliye serial nahi likhi).
_ASMA = """\
Ar-Rahman|The Most Compassionate
Ar-Raheem|The Most Merciful
Al-Malik|The King
Al-Quddus|The Most Pure
As-Salam|The Source of Peace
Al-Mu'min|The Giver of Security
Al-Muhaymin|The Guardian
Al-Aziz|The Almighty
Al-Jabbar|The Compeller
Al-Mutakabbir|The Supreme
Al-Khaliq|The Creator
Al-Bari|The Maker
Al-Musawwir|The Fashioner
Al-Ghaffar|The Forgiver
Al-Qahhar|The Subduer
Al-Wahhab|The Giver of Gifts
Ar-Razzaq|The Provider
At-Tawwab|The Acceptor of Repentance
Al-Fattah|The Opener
Al-Aleem|The All-Knowing
Al-Qabid|The Withholder
Al-Basit|The Extender
Al-Khafid|The Abaser
Ar-Rafi|The Exalter
Al-Muizz|The Giver of Honour
Al-Mudhill|The Giver of Dishonour
As-Sami|The All-Hearing
Al-Baseer|The All-Seeing
Al-Hakam|The Judge
Al-Adl|The Just
Al-Latif|The Gentle
Al-Khabir|The All-Aware
Al-Halim|The Forbearing
Al-Azim|The Magnificent
Al-Ghafoor|The Great Forgiver
Ash-Shakur|The Appreciative
Al-Aliyy|The Most High
Al-Kabir|The Greatest
Al-Hafiz|The Preserver
Al-Muqit|The Sustainer
Al-Hasib|The Reckoner
Al-Jalil|The Majestic
Al-Karim|The Generous
Ar-Raqib|The Watchful
Al-Mujeeb|The Responsive
Al-Wasi|The All-Encompassing
Al-Hakim|The All-Wise
Al-Wadud|The Loving
Al-Majid|The Glorious
Al-Baith|The Resurrector
Ash-Shahid|The Witness
Al-Haqq|The Absolute Truth
Al-Wakil|The Trustee
Al-Qawiyy|The All-Strong
Al-Matin|The Firm
Al-Waliyy|The Protecting Friend
Al-Hameed|The Praiseworthy
Al-Muhsi|The Enumerator
Al-Mubdi|The Originator
Al-Mueed|The Restorer
Al-Muhyi|The Giver of Life
Al-Mumeet|The Bringer of Death
Al-Hayy|The Ever-Living
Al-Qayyum|The Self-Subsisting
Al-Wajid|The Finder
Al-Majeed|The Noble
Al-Wahid|The One
Al-Ahad|The Unique
As-Samad|The Eternal Refuge
Al-Qadir|The All-Capable
Al-Muqtadir|The All-Determiner
Al-Muqaddim|The Expediter
Al-Muakhkhir|The Delayer
Al-Awwal|The First
Al-Akhir|The Last
Az-Zahir|The Manifest
Al-Batin|The Hidden
Al-Wali|The Governor
Al-Mutali|The Most Exalted
Al-Barr|The Source of Goodness
Al-Muntaqim|The Avenger
Al-Afuww|The Pardoner
Ar-Rauf|The Most Kind
Malik-ul-Mulk|Owner of All Sovereignty
Dhul-Jalali-wal-Ikram|Lord of Majesty and Generosity
Al-Muqsit|The Equitable
Al-Jami|The Gatherer
Al-Ghani|The Self-Sufficient
Al-Mughni|The Enricher
Al-Mani|The Preventer
Ad-Darr|The Distresser
An-Nafi|The Bestower of Benefit
An-Nur|The Light
Al-Hadi|The Guide
Al-Badi|The Incomparable Originator
Al-Baqi|The Everlasting
Al-Warith|The Inheritor
Ar-Rasheed|The Guide to Right Path
As-Sabur|The Most Patient"""
