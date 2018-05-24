COMPILER=latexmk
NAME=homework

all: $(NAME).tex
	$(COMPILER) -pdf -pdflatex="pdflatex -shell-escape -enable-write18" \
		-use-make -auxdir=auxFile -outdir=auxFile $(NAME).tex ;
	shopt -s extglob ;
	cp auxFile/*.pdf ./
	
show: $(NAME).pdf
	make all;
	open $(NAME).pdf

clean:
	rm -rf ./auxFile
