# Questões de Medicina Legal – Provas de Concursos

**Resultado:** [`resultado/Questoes_Medicina_Legal_Provas_de_Concursos.pdf`](resultado/Questoes_Medicina_Legal_Provas_de_Concursos.pdf)
(605 páginas, organizado por prova, com índice, marcadores e gabarito oficial quando disponível).

As questões foram **recortadas diretamente dos cadernos originais** (pastas `P1/` e `p2/`), sem redigitação —
enunciados, alternativas, numeração, figuras e tabelas aparecem exatamente como na prova.

## Relatório

| Item | Quantidade |
|---|---|
| Arquivos analisados | 69 (35 de prova, 34 de gabarito) |
| Provas distintas | 33 (2 arquivos eram cópias idênticas) |
| Provas com questões de Medicina Legal | 32 |
| Questões de Medicina Legal | 1.317 |
| Com gabarito localizado | 1.209 (31 anuladas no gabarito oficial) |
| Sem gabarito localizado | 108 (100 da PEFOCE AVA + 8 discursivas) |

**Sem questões de Medicina Legal:** `pv_discursiva_cargo_4_medico_legista.pdf` (SDS/PE 2016 – conteúdo sobre
silicose e manutenção de máquinas; parece ser de outro cargo).

**Cópias idênticas (incluídas uma vez):** `policia_civil_medico_legista_caderno_01.pdf` = `medico_legista (3).pdf`;
`s22_01_…medico (1).pdf` = `s22_01_…medico.pdf`.

**Observações**
- Gabarito apenas **preliminar** na pasta: POLITEC/MT 2022 (2 provas), PC-RR 2022, PTC-GO 2024 (2), SESACRE M29, PEFOCE 2011, SDS/PE 2016.
- O gabarito AVA da pasta é do cargo Perito Criminal e não corresponde à prova de Médico Perito Legista (PEFOCE AVA).
- Banca/ano ausentes nos arquivos constam como "não identificado".
- PCDF 2008 é digitalizada e contém marcações manuscritas; a prova FCC 2006 é a versão com respostas marcadas.
- Nas questões 40–50 da FCC 2006 foi incluída a chave de respostas compartilhada ("Atenção: … use a chave abaixo").

## Como regenerar

Requer Python com `pymupdf` e `tesseract-ocr` (português) para a prova digitalizada.

```bash
python3 tools/render.py resultado/Questoes_Medicina_Legal_Provas_de_Concursos.pdf
```

- `tools/locate.py` – localiza questões e suas regiões nas páginas
- `tools/sel.txt` – questões selecionadas por prova
- `tools/provas.py` – metadados (concurso, órgão, cargo, banca, ano)
- `tools/gab.py` – extração dos gabaritos oficiais
- `tools/pcdf_regions.json` – regiões da prova digitalizada (PCDF 2008)
- `tools/qa.py`, `tools/qa2.py` – verificações automáticas de recortes
