pyreverse .\engines\ .\article.py .\bot.py .\corpus_creator.py .\db.py .\logs.py .\config.py .\oar.py .\pdf.py .\scrapper.py .\permission.py -o png
move classes.png documentation\classes.png
move packages.png documentation\packages.png

python -m pydoc -w permission
move permission.html documentation\permission.html

python -m pydoc -w article
move article.html documentation\article.html

python -m pydoc -w bot
move bot.html documentation\bot.html

python -m pydoc -w config
move config.html documentation\config.html

python -m pydoc -w corpus_creator
move corpus_creator.html documentation\corpus_creator.html

python -m pydoc -w db
move db.html documentation\db.html

python -m pydoc -w logs
move logs.html documentation\logs.html

python -m pydoc -w oar
move oar.html documentation\oar.html

python -m pydoc -w pdf
move pdf.html documentation\pdf.html

python -m pydoc -w scrapper
move scrapper.html documentation\scrapper.html

python -m pydoc -w engines
move engines.html documentation\engines.html

python -m pydoc -w engines\engine.py
move engine.html documentation\engines.engine.html