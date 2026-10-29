# Contributing to Open Case

Thank you for helping. You can contribute a case, a translation, or a fix to the exporter.

## Licenses

- **Cases and anything creative** (cases, texts, images, diagrams, design guide): by opening a pull request you agree to publish your work under **CC BY-NC-SA 4.0** (`LICENSE-CONTENT`).
- **Code, scripts and docs**: **MIT** (`LICENSE`).
- You confirm that you wrote the work, or that you have the right to share it under these licenses.
- The Open Case name and logo stay reserved to the project (see `NOTICE`). You can say your case is "made with the Open Case format".

## Contributing a case

1. Copy `cases/chupacabras-labranza/` to `cases/<your-case>/` and replace its content. The format is in `docs/case-format.md`.
2. Write the truth first: what happened, who did it, how and why. Keep it in the guide, not in anything the teams will see.
3. Keep the team material (kit, dossier sheets handed out to everyone) free of the solution. The exporter puts `teams/` and `director/` in separate folders; check that nothing in `teams/` gives the culprit away.
4. Characters, companies and events must be fictional. No recognisable real people, and no portrait with a recognisable face.
5. If you use AI-generated images, say so in a `README.md` inside your case folder, and do not use images you have no right to share.
6. Validate: `python export.py cases/<your-case> --check`. It reports the file and line of each problem.
7. Export and look at every PDF: `python export.py cases/<your-case>` (the PDFs are in `output/`). Print one sheet at 100 % to see the size of the cards.
8. Play it with real people before you submit. Cases get fixed by playing them.
9. Open a pull request. Describe the case in a few lines: setting, number of teams, duration, language.

## Translations

Add `languages/<lang>/` with the same file names as the base language, and add the language to the `languages:` list in the case's `case.yaml`. `python export.py cases/<case> --lang <lang> --check` checks that nothing is missing. Keep codes (`B1`, `E01`) identical across languages. To add a language to the exporter itself (the words it prints), add `opencase/strings/<lang>.yaml`.

## Exporter changes

- Code, comments, option names and messages are in English.
- Keep the design system's class names as they are (`oc-...`); they come from the published design guide.
- Before you open the pull request, export the sample case and compare the result; a change that is not meant to alter the output should leave the generated HTML unchanged.
- Run `python export.py cases/chupacabras-labranza --check` and an export of the sample case.
