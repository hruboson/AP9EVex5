- swarmový princip
- podobná myšlenka jako u PSO
- máme jedince, který je v populaci nejlepší - **global best**
    - ostatní jedinci mají tendenci prohledávat k němu (k global bestu)
    - nejdou tam přímo ale dělají **kroky** po určité vzdálenosti a v každém kroku ohodnotí
        - přesunou se tam, kde najde lepší hodnotu, pokud nenajde tak zůstane na místě
        - počet kroků je přesně předdefinován - jen se mění jejich délka aby se "vlezly mezi sebe a besta"
- použití perturbačního vektoru - určuje ve které dimenzi se má pohybovat (např. v dvoudimenzionálním má možnost, přes x, přes y, přes x&y)
- zase za mezemi neohodnocuju

1. STRATEGIE - all to one/all to best, all to random, all to all (vyčerpávající - vpodstatě bruteforce)
2. PATHLENGTH - většinou > 1, abychom prohledávali i za tím za kým směřujem, 3 znamená že pujde k bestu a potom 2x délku cesty k němu za ním
3. STEP - délka kroku, poměrově k délce cesty např. 0.3 - po každé zhruba třetině cesty ohodnotím, číslo by němelo být přesným dělitelem 1 (aby nešly přímo na body co už máme ohodnocené)
4. PRT vektor - pravděpodobnost toho, že v dimenzi následujeme trajektorii (perturbační vektor), vektor 0 a 1, vychází ze vzorce

(na přednášce ta goofy 2000s vizualizace videjko)

