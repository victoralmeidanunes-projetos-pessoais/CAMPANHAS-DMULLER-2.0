@echo off
cd /d "C:\Users\victor.n\PROJETO"

echo ============================
echo ENVIANDO ATUALIZACOES...
echo ============================

git add .

git commit -m "%date% %time%"

git push

exit

###colocar isso no whatdogs

