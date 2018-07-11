import matplotlib.pyplot as plt
import sys

class Results(object):

    def __init__(self, resultsFilePath, outputDir):
        self.resultsFilePath = resultsFilePath
        self.outputDir = outputDir
        self.numEpochs = 0
        self.learningRates = []
        self.perplexities = []
        self.epochs = []
        self.parse()
        self.bestPerplexity = self.perplexity[-1]

    def parse(self):
        with open(self.resultsFilePath, 'r') as file:
            for line in file:
                if(line.startswith('epoch')):
                        self.numEpochs += 1
                elif(line.startswith('development')):
                    self.parseDevelopment(line[:-1])
            self.epochs = list(range(self.numEpochs))

    def parseDevelopment(self, line):
        self.learningRates.append(float(line.split()[7].replace(",","")))
        self.perplexities.append(float(line.split()[3].replace(",","")))

    def plot(self):
        fig, (ax1, ax2)  = plt.subplots(2)

        ax1.plot(self.epochs, self.learningRates)
        ax1.set(xlabel='epoch',ylabel='learning rate')
        ax1.grid()

        ax2.plot(self.epochs, self.perplexities)
        ax2.set(xlabel='epoch',ylabel='perplexity')
        ax2.grid()

        fig.savefig(outputDir + '/resultsPlotted.png')

    def writeBestPerplexity(self):
        with open(outputDir + 'bestPerplexity.txt','w') as file:
            file.write(str(self.bestPerplexity))
            

if __name__ == "__main__":
    resultsFilePath=str(sys.argv[1])
    outputDir=str(sys.argv[2])
    result = Results(resultsFilePath)
    result.plot()
    result.writeBestPerplexity()
