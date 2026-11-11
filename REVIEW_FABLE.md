# Revue complète par Fable 5.2 (2026-11-11)

Note interne, à retirer avant de rendre le dépôt public.

- **Point de départ :** commit `fc8cb7f`, dernière version faite par Opus 5.5.
- **Méthode :** `make reproduce` puis `make refresh` depuis le dépôt propre ; chaque chiffre de `README.md`, `REPORT.md`, `FAQ.md` et du dashboard comparé aux sorties de `data/processed/` ; chaque lien de causalité relu comme le ferait un juge.
- **Résultat des tests :** 6 passent, avant et après.

## Contexte à connaître pour comparer les deux modèles

- Le prompt programmé de 4h45 a d'abord été reçu par Opus 5.5, interrompu au bout de quelques minutes. Ses modifications non commitées sont dans la branche locale `opus-night-wip` (non poussée). Je suis reparti de `fc8cb7f` sans les reprendre.
- Je partage la conversation avec Opus : je savais donc qu'il avait repéré la série `revenueSeries` sur revenue.near.org. La trouvaille est la sienne. La lecture que j'en fais est différente (voir le point 4 ci-dessous).

## Les changements qui comptent

### 1. La régression sur les swaps confidentiels était présentée comme plus solide qu'elle ne l'est

- **Avant :** « 0,7 bps × public + 12 bps × confidentiel », intervalle 10,8–14,5, et « les swaps confidentiels expliquent la majeure partie de la hausse ». Ces chiffres dataient en plus d'un ancien calcul sur 12 semaines.
- **Maintenant :** 1,0 et 11,0 bps sur 13 semaines (intervalle 9,7–13,4). J'ai ajouté trois tests de robustesse :
  - en retirant une semaine à la fois : 10,7 à 12,2 bps ;
  - avec une constante : elle vaut environ zéro ;
  - sur les variations d'une semaine à l'autre : **5,5 bps** (intervalle 2,2–9,0), et 2,9 sur le public.
- **Pourquoi :** 13 points, et les deux volumes montent sur la période. Une régression en niveaux peut capter une tendance commune. Sur les variations, la prime est deux fois plus faible, et le chiffre de Dune (7,4 bps) tombe dans l'intervalle.
- **Conséquence :** la part de la hausse du take (août → octobre, +3,3 bps) expliquée par le passage au confidentiel va de 22 % à 84 % selon la méthode (54 % avec le chiffre de Dune). Le rapport dit maintenant « le principal facteur identifié, entre un cinquième et cinq sixièmes ».
- **Preuve :** `make confidential`, champs `regression.robustness` et `jump_explained` de `data/processed/confidential_summary.json`.

### 2. La causalité « l'airdrop paie cette croissance » était affirmée, pas démontrée

- **Avant :** titres et résumés du type « confidential swaps, which an incentive is paying for ».
- **Maintenant :** « coincides with », « grew under an incentive », et la FAQ dit que la cause n'est pas prouvée.
- **Pourquoi :** la seule preuve est la chronologie. Il n'y a pas de groupe témoin, et near.com a lancé d'autres produits sur la même période. Le titre du rapport (« partly bought ») reste défendable ; les phrases catégoriques ne l'étaient pas.

### 3. « In NEAR terms the two cancel » était faux sur les données actuelles

- **Avant :** surplus de revenus de $1,72M, soit 408k NEAR, contre 333k NEAR distribués : « les deux s'annulent ».
- **Maintenant :** surplus de $1,87M, soit 479k NEAR, contre 333k : un net de 146k NEAR, 0,01 % de l'offre. Le Drop 1 a coûté environ les trois quarts du surplus.
- **Pourquoi :** les données des portefeuilles ont été complétées depuis le premier calcul, et le texte n'avait pas suivi. J'ai aussi ajouté que ce calcul est la lecture favorable : il attribue tout le surplus à l'incitation et ne compte que le Drop 1.
- **Preuve :** champ `near_terms` du même fichier.

### 4. Le site de NEAR publie un deuxième chiffre de revenus, environ 20 % au-dessus des portefeuilles

- **Trouvé par Opus** pendant son passage interrompu. Il en concluait que la baisse de novembre n'était peut-être qu'un décalage (5,9 bps selon NEAR contre 3,9 chez nous).
- **Ma lecture :** ce 5,9 est un artefact. Le revenu du mois en cours sur le site va jusqu'à la veille, alors que les séries de volume et de frais s'arrêtent un à deux jours plus tôt. En alignant les jours, le rapport entre la série de NEAR et les portefeuilles est stable : 1,21 en août, 1,23 en septembre, 1,14 en octobre, 1,18 en novembre.
- **Conséquence :** les deux définitions montrent la même baisse d'environ 30 % début novembre. Elle est donc confirmée par trois sources (portefeuilles 3,9 bps, DefiLlama 3,8, série de NEAR environ 4,6 contre 6,3 en octobre).
- **Ce qui reste inexpliqué :** où vont ces 20 %. Le total cumulé de la série de NEAR est de 5,03M NEAR ; son propre tableau des portefeuilles, et notre reconstruction, donnent 4,30M. Ce ne sont pas des frais en attente : le compte collecteur dans `intents.near` ne contenait qu'environ $400 le 11 novembre.
- **Preuve :** `make official`, champ `revenue_definitions` de `data/processed/official_crosscheck.json`.

### 5. Erreurs de logique

- **FAQ :** le rejet de H4.1 était présenté comme « contre le scénario haussier ». C'est l'inverse : H4.1 prévoyait que la TVL partirait après le snapshot ; elle a doublé, ce qui est favorable à NEAR.
- **Critères d'invalidation :** la section « What would change our mind » listait des critères qui, s'ils se déclenchaient, aggraveraient le constat au lieu de le contredire. Le texte dit maintenant que ce sont des alertes sur la qualité du revenu, et renvoie aux catalyseurs pour ce qui changerait la conclusion en faveur de NEAR.
- **Dashboard :** « the base case never reaches break-even » alors que 5 % des trajectoires y arrivent. Remplacé par « the median path stays far below break-even ».

## Liste complète, fichier par fichier

### `src/analysis/confidential.py`
| Changement | Raison |
| --- | --- |
| Ajout de `regression.robustness` (variations hebdomadaires, retrait d'une semaine, constante) | Tester si la régression en niveaux capte une tendance commune |
| Ajout de `jump_explained` | Rendre reproductible la part de la hausse expliquée, sous trois hypothèses de prime |
| Ajout de `near_terms` | Rendre reproductible la comparaison en NEAR (479k contre 333k) |
| Test hors échantillon aussi calculé avec la régression sur variations ($0,47M prédit) | Montrer que l'écart va de 1,3× à 2,5× selon la version |

### `src/analysis/official.py`
| Changement | Raison |
| --- | --- |
| Lecture de `revenueSeries` et des taux de capture par mécanisme | Deuxième définition du revenu ; hausse répartie sur trois mécanismes |
| Champ `revenue_definitions` : ratio mensuel série de NEAR / portefeuilles, sur des jours alignés | Comparer les tendances sans l'artefact de dates |
| Totaux des portefeuilles comparés jusqu'au jour de la capture | Avant : filtre sur la date de la série de volume, en retard d'un à deux jours ; l'écart passait à 0,38 % sans raison |

### `src/analysis/montecarlo.py` et `tests/test_montecarlo.py`
| Avant | Maintenant | Raison |
| --- | --- | --- |
| Scénario « take doubles again (11 bps) » | « take doubles again » | L'étiquette était figée ; le take simulé est de 9,9 bps |
| Première ligne de la table de sensibilité : $135M/jour, figé | Volume de départ de la simulation ($130M) | Chiffre périmé |
| Test lié à la valeur 135 | Lit la valeur dans la table et vérifie qu'elle correspond au volume de départ | Suivre le changement |

### `src/analysis/dashboard_data.py` et `dashboard/index.html`
| Avant | Maintenant | Raison |
| --- | --- | --- |
| « reconciles to the chain within 0.1% » | « within 1% » (0,6 % mesuré) | Chiffre d'octobre |
| « growing, mostly through confidential swaps that an airdrop campaign is paying for » | « grew sharply from September, as confidential swaps took off under an airdrop campaign, and has eased since » | Causalité, et baisse de novembre |
| Parts des intégrateurs « last 30 days to 2026-11-09 » | « 30 days to 2026-10-29 » (champ `oneclick_as_of`) | La collecte 1Click s'arrête le 29 octobre |
| Tableau H1.1 : $7,29M contre $7,30M | $7,96M contre $8,01M, ratio 0,994 | Chiffre d'octobre |
| Tableau H1.2 : « 1.6% left the wallets » | 57 036 NEAR, 1,3 % de ce qu'ils ont reçu | Base de calcul ambiguë |
| Tableau H5.1 : 5 % « also with the issuance cut » | 17 % et 5 % ; 18 % et 6 % avec la baisse d'émission | Le chiffre avec baisse était faux d'un point |
| Graphique des pairs incluant JTO à 18 191× | Pairs avec au moins $100k de revenus sur 30 jours | $825 de revenus : pas un comparable, et la barre sortait de l'écran sur mobile |
| « NEAR Intents won its category on volume » | « led its category from May to October (THORChain is ahead in November so far) » | Donnée de novembre |
| Carte de comparaison avec NEAR : trois chiffres | Quatrième chiffre : série de revenus de NEAR / portefeuilles | Point 4 |
| Carte confidentielle : ajustement et test hors échantillon en niveaux seulement | Les deux versions (5,5 bps sur variations ; écart de 1,3× à 2,5×) | Point 1 |
| Description d'aperçu de lien : « 0.1% », « about a fifth » | « within 1% », « about a sixth » | Cohérence |

### `REPORT.md`
| Avant | Maintenant |
| --- | --- |
| Régression 12 semaines, 0,7 / 12 bps, 10,8–14,5 | 13 semaines, 1,0 / 11,0, 9,7–13,4, plus les tests de robustesse |
| « pay NEAR roughly 7–12 bps, against under 1 bp » | « about 5 to 11 bps against 1 to 3 » |
| « Most of the rise comes from confidential swaps » | « The largest identified driver » ; 84 % / 54 % / 22 % selon la méthode |
| $7 287 030 contre $7 295 035 (0,999) | $7 960 601 contre $8 008 957 (0,994), au 10 novembre |
| Portefeuilles 60 / 32 / 8 % | 61 / 32 / 7 % |
| « one fifth », « 16 NEAR per 100 » | « one sixth », 15 selon l'audit, 16 selon NEAR |
| Surplus $1,72M, 1,2× le Drop 1, « the two cancel » | $1,87M, 1,35×, net de 146k NEAR |
| Fin de l'incitation : 10 % ; extinction sur 6 mois : 11 % (texte) | 9 % et 10 %, comme dans le tableau |
| Pairs : médiane 22×, NEAR 212×, $0,6B contre $5,6B | 20×, 220×, $0,45B contre $4,9B |
| Parts cross-chain « 61–79% each month since May » | 58–79 % de mai à octobre ; novembre à date 35 %, signalé sans conclure |
| 692 jours sous l'eau ; stakers 45 %, 5,3 % ; offre +2,0 % | 703 ; 44 %, 5,5 % ; +2,1 % |
| « $124M now », « $600M » | « about $130M », « $620M » (cohérent avec la section 5) |
| Semaine de novembre : une source | Dix jours, trois sources |
| Tableau des critères cassé par une ligne vide | Corrigé |
| Rien sur les hypothèses du Monte Carlo | Quatre lignes : take fixe, tirages du passé, émission, biais optimiste mesuré |
| Rien sur l'écart de 20 % avec la série de NEAR | Paragraphe dans la section 1, et question ajoutée à la liste pour NEAR |

### `README.md` et `FAQ.md`
Mêmes corrections de chiffres que le rapport, plus :
- README : « the first drop about equals the revenue uplift » → « cost about three quarters of the revenue uplift » ; « NEAR-for-NEAR, the two cancel » → « the net is 0.01% of supply » ; la ligne `make confidential` citait encore 0,65 / 12,2 bps.
- FAQ : réponse sur H4.1 corrigée (point 5) ; « So most of the uplift is roughly what the incentive cost » remplacé par le chiffre et la réserve sur la causalité ; réponse sur l'écart 11 bps / 7,4 bps réécrite avec le résultat sur variations.

### `RESEARCH_LOG.md`
Entrée 32 : toutes les corrections ci-dessus, datées.

### `data/`
Captures du 2026-11-11 (`make refresh`) et sorties recalculées. Aucun changement de méthode dans la collecte.

## Vérifié et trouvé correct, sans rien changer

- Reconstruction des revenus contre DefiLlama : ratio 0,994, chaque mois complet à ±5 %.
- Émission nette de 2,43 % par an ; seuils de 41× et 64×.
- Compensation de l'émission de février à octobre : 14,8 % (NEAR : 16,3 %).
- Tableau Monte Carlo de la section 5 : identique aux sorties.
- H4.1 : la conclusion tient aussi avec la date enregistrée du 17 septembre ($79M → $152M trente jours après). Le code utilise le 16.
- SwapKit : 40 % du volume, 71 % des frais d'apps, 1 % des revenus de NEAR. Répartition par actif. Métriques de risque.
- Affirmation « le prix a été multiplié par plus de 4 de février à octobre » : $1,06 → $4,90.
- Actualité au 11 novembre : rien de nouveau sur un Drop 2, sur la ratification ou la date de HSP-029, ni sur les frais d'Intents.
- Dashboard : aucune erreur JavaScript, aucun débordement de page à 390 px et 1440 px. La seule requête en échec est la lecture du `data.json` sur GitHub, normale tant que le dépôt est privé.

## Ce que j'ai hésité à changer, et pourquoi je ne l'ai pas fait

- **Le titre « Growing, but partly bought ».** Après le point 1, « bought » est plus fragile. Je l'ai gardé parce que « partly » est exact et que le corps du texte porte maintenant les réserves. À toi de voir si tu préfères « partly incentive-driven ».
- **Relancer la collecte 1Click jusqu'en novembre.** Les parts des intégrateurs datent du 29 octobre. L'API est très lente (environ 1 000 swaps par minute) ; j'ai préféré dater les chiffres plutôt que les rafraîchir.
- **La date du snapshot (16 ou 17 septembre).** `HYPOTHESES.md` dit le 17, le code le 16. La conclusion est la même ; je n'ai pas touché au code pour ne pas décaler tous les chiffres d'un jour sans bénéfice.
- **Les 0,6 de `retired_share`** (scénario « buyback wallet only »). C'est figé dans le code alors que la part réelle est de 61 %. Écart négligeable.
- **Le volume de départ.** Le rapport disait $124M (moyenne brute sur 30 jours) et la simulation part de $130M (moyenne lissée). J'ai aligné le texte sur la simulation plutôt que de changer le modèle.
- **`data.json` commité par le robot** ne se reproduit pas exactement depuis les captures commitées, parce que le robot ne commite que ce fichier. Sans conséquence pour un juge qui lance `make reproduce`, mais à savoir.

## Ce qui reste ouvert

1. Où vont les 20 % d'écart entre la série de revenus de NEAR et les trois portefeuilles. À ajouter à ta demande au support de near.com.
2. La commission réelle sur les swaps confidentiels : entre 5 et 11 bps selon la méthode, 7,4 selon Dune. Toujours pas de réponse de NEAR.
3. THORChain devant NEAR Intents en novembre selon DefiLlama (8 jours) : à revérifier avant la soumission.
4. Les chiffres de la section 5 bougent chaque jour avec le refresh. À regeler la veille de la soumission.
5. Ce fichier et la branche locale `opus-night-wip` sont à retirer avant de rendre le dépôt public.
