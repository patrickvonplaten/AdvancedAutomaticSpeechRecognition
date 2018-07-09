#!/usr/bin/env python3
import gzip
import math
import sys
import os
from operator import attrgetter

class Node(object):

    def __init__(self, index, time):
        self.index = index
        self.startTime = time
        self.incomingEdges = []
        self.outgoingEdges = []
        self.forwardProb = None
        self.backwardProb = None
        self.endTime = None

    def addToIncomingEdges(self, edge):
        self.incomingEdges.append(edge)

    def addToOutgoingEdges(self, edge):
        self.outgoingEdges.append(edge)

    def setForwardProb(self, p):
        self.forwardProb = p

    def setBackwardProb(self, p):
        self.backwardProb = p

    def setEndTime(self):
        if(self.outgoingEdges):
            self.endTime = getattr(max(self.outgoingEdges, key=attrgetter('endTime')),'endTime')
        else:
            self.endTime = self.startTime

class Edge(object):

    def __init__(self, index, nodeFrom, nodeTo, word, acousticScore, languageScore, lmScale):
        self.index = index
        self.nodeFrom = nodeFrom
        self.nodeTo = nodeTo
        self.word = word
        self.acousticScore = acousticScore
        self.languageScore = languageScore
        self.weight = self.acousticScore + lmScale * self.languageScore
        self.posteriorProb = None
        self.startTime = None
        self.endTime = None
        self.confidenceMeasure = float('inf')

    def setNegativeLogPosteriorProb(self, posteriorProb):
        self.posteriorProb = posteriorProb

    def setStartEndTimes(self, nodes):
        self.startTime = nodes[self.nodeFrom].startTime
        self.endTime = nodes[self.nodeTo].startTime

class WordGraph(object):

    def __init__(self, latticeFilePath, startTime, code, resultFilePath, confMeasFilePath, pruningThreshold, lmScale, mode):
        self.mode = mode
        self.nodes = []
        self.edges = []
        self.encodedResults = []
        self.lmScale = lmScale 
        self.numNodes = None
        self.numEdges = None
        self.fullPathProb = None
        self.startTime = float(startTime)
        self.bestNegativeLogPosteriorProb = None
        self.timeWordPosteriors = None
        self.pruningThreshold = pruningThreshold
        self.code = code
        self.resultFilePath = resultFilePath
        self.confMeasFilePath = confMeasFilePath
        self.confMeasFilePath = confMeasFilePath
        self.parseLattice(latticeFilePath)
        self.setNodesEndTime()
        self.endTime = self.nodes[-1].endTime
        self.runForwardBackwardAlgorithm()
        self.calculateTimeFrameWordPosteriors()
        self.calculateMeanConfidenceMeasures()
#        Rescoring makes the score worse in my case
#        self.rescoreWordGraph()
        self.pruneWordGraph()
        self.decodeWordGraph()
        self.writeResultsToCTMFile()
        self.writeConfidenceMeasuresToFile()
        for edge in self.edges:
            assert edge.startTime == self.nodes[edge.nodeFrom].startTime

    def setNodesEndTime(self):
        for node in self.nodes:
            node.setEndTime()

    def getWordGraphDensity(self):
        return self.numEdges/float(self.words)

    def parseLattice(self, latticeFilePath):
        with gzip.open(latticeFilePath, 'rb') as file:
            for line in file:
                line = self.convertToRegString(line)
                lineType = self.getLineType(line)
                if(lineType == 'edge'):
                    edge = self.parseEdge(line)
                    edge.setStartEndTimes(self.nodes)
                    self.nodes[edge.nodeFrom].addToOutgoingEdges(edge)
                    self.nodes[edge.nodeTo].addToIncomingEdges(edge)
                    self.edges.append(edge)
                elif(lineType == 'node'):
                     self.nodes.append(self.parseNode(line))
                elif(lineType == 'lmScale'):
                    if(self.lmScale == None):
                        self.lmScale = self.parseLmScale(line)
        self.numNodes = len(self.nodes)
        self.numEdges = len(self.edges)

    def convertToRegString(self, line):
        return str(line[:-1],'utf-8')

    def getLineType(self, line):
        if(line.startswith('J=')):
            return 'edge'
        elif(line.startswith('I=')):
            return 'node'
        elif(line.startswith('lmscale=')):
            return 'lmScale'
        else:
            return None

    def parseEdge(self, line):
        lineArray = [x[2:] for x in line.split()] 
        assert self.lmScale is not None, 'lmScale should be defined before the edges in the lattice file'
        return Edge(index=int(lineArray[0]), nodeFrom=int(lineArray[1]), nodeTo=int(lineArray[2]), word=lineArray[3], acousticScore=-float(lineArray[5]), languageScore=-float(lineArray[6]), lmScale=self.lmScale)

    def parseNode(self, line):
        lineArray = [x[2:] for x in line.split()] 
        return Node(index=int(lineArray[0]), time=float(lineArray[1]))
        
    def parseLmScale(self, line): 
        return float(line.split('=')[1])

    def runForwardBackwardAlgorithm(self):
        self.nodes[0].forwardProb = 0 
        self.calculateProbability(self.nodes, 'forwardProb', 'incomingEdges', 'nodeFrom')
        self.nodes[-1].backwardProb = 0 
        self.calculateProbability(self.nodes[::-1], 'backwardProb', 'outgoingEdges', 'nodeTo')
        assert math.isclose(self.nodes[0].backwardProb, self.nodes[-1].forwardProb, abs_tol=1e-6), "Probability should be the same!"
        self.fullPathProb = self.nodes[0].backwardProb

        bestNegativeLogPosteriorProb = float('inf')
        if self.mode == 'log semiring':
            fullPathProb = self.fullPathProb
        elif self.mode == 'tropical semiring':
            fullPathProb = 0

        for edge in self.edges:
            negativeLogPosteriorProb = self.nodes[edge.nodeFrom].forwardProb + edge.weight + self.nodes[edge.nodeTo].backwardProb - fullPathProb
            edge.setNegativeLogPosteriorProb(negativeLogPosteriorProb)
            if(negativeLogPosteriorProb < bestNegativeLogPosteriorProb):
                bestNegativeLogPosteriorProb = negativeLogPosteriorProb
        self.bestNegativeLogPosteriorProb = bestNegativeLogPosteriorProb

    def calculateProbability(self, nodes, probabilityType, nameOfEdgesList, nodeType):
        for node in nodes[1:]:
            value = float('inf') 

            for edge in getattr(node, nameOfEdgesList):
                edgeNode = self.nodes[getattr(edge, nodeType)]
                value = self.getValueSum(value, getattr(edgeNode, probabilityType) + edge.weight)     
                assert value > 0, "negative log probability cannot be < 0" 
            setattr(node, probabilityType, value)

    def getValueSum(self, value, summedProb):
        if self.mode == 'log semiring':
            if value == float('inf'):
                return summedProb 
            else:
                return max(0, - (math.log(1 + math.exp(-abs(summedProb - value))) - min(summedProb, value)))
        elif self.mode == 'tropical semiring':
            return min(value, summedProb)
    
    def calculateMeanConfidenceMeasures(self):
        for edge in self.edges:
            start = int(round(100*edge.startTime))
            end = int(round(100*edge.endTime))
            for time in range(start, end):
                edge.confidenceMeasure = self.getValueSum(self.timeWordPosteriors[time][edge.word], edge.confidenceMeasure)
            edge.confidenceMeasure += math.log(end - start)

    def rescoreWordGraph(self):
        for edge in self.edges:
            edge.weight = max(edge.confidenceMeasure,0)
        self.runForwardBackwardAlgorithm()

    def calculateTimeFrameWordPosteriors(self):
        numTimeInstances = int(self.endTime * 100)
        timeWordPosteriors = [None] * numTimeInstances 

        for timeInstance in range(numTimeInstances): 
            timeWordPosteriors[timeInstance] = self.fillTimeFrameDictionary(timeInstance/100.0)
        self.timeWordPosteriors = timeWordPosteriors

    def fillTimeFrameDictionary(self, timeInstance):
        d = {} 
        edgesAtTimeInstance = []
        for node in self.nodes:
            if(node.startTime <= timeInstance and node.endTime > timeInstance):
                edgesAtTimeInstance += node.outgoingEdges
        for edge in edgesAtTimeInstance: 
            if(edge.word in d):
                d[edge.word] = self.getValueSum(edge.posteriorProb, d[edge.word])
            else:
                d[edge.word] = edge.posteriorProb
        return d

    def pruneWordGraph(self):
        for idx, edge in enumerate(self.edges):
            threshold = self.bestNegativeLogPosteriorProb + self.pruningThreshold
            if(edge.posteriorProb > threshold):
                del self.edges[idx]
        self.numEdges = len(self.edges)

    def decodeWordGraph(self):
        node = self.nodes[0]
        while(len(node.outgoingEdges) is not 0):
            bestEdge = min(node.outgoingEdges, key=attrgetter('posteriorProb'))
            node = self.nodes[bestEdge.nodeTo]
            startTime = bestEdge.startTime + self.startTime
            timeDiff = bestEdge.endTime - bestEdge.startTime  
            self.encodedResults.append((bestEdge.word[1:-1], round(startTime, 3), round(timeDiff, 3), bestEdge.confidenceMeasure))

    def writeConfidenceMeasuresToFile(self):
        with open(self.confMeasFilePath, 'a') as confMeasFile:
            for tupleResult in self.encodedResults:
                confMeasFile.write('Word: ' + tupleResult[0] + '| Confidence Measure: ' + str(tupleResult[3]) + '\n')

    def writeResultsToCTMFile(self):
        with open(self.resultFilePath, 'a') as resultFile:
            resultFile.write(";; <name> <track> <start> <duration> <word>\n")
            resultFile.write(";; QRBC_ENG_GB_20110106_104800_BBC_PHONEIN_POD/QRBC_ENG_GB_20110106_104800_BBC_PHONEIN_POD"+self.code+" ("+str(self.startTime)+"-" + str(self.endTime) +")\n")
            for tupleResult in self.encodedResults:
                if(tupleResult[0] != "!NULL" and tupleResult[0] != "[SILENCE]" and tupleResult[0] != "[NOISE]"):
                    resultFile.write("QRBC_ENG_GB_20110106_104800_BBC_PHONEIN_POD 1 " + str(tupleResult[1]) + " " + str(tupleResult[2]) + " " + tupleResult[0] + "\n")
            
    def printInformation(self):
        print("Num nodes",self.numNodes)
        print("Num edges", self.numEdges)
        print("Incoming Edges First Node",[ x.index for x in self.nodes[0].incomingEdges])
        print("Outgoing Edges First Node",[ x.index for x in self.nodes[0].outgoingEdges])
        print("Incoming Edges Last Node",[ x.index for x in self.nodes[-1].incomingEdges])
        print("Outgoing Edges Last Node",[ x.index for x in self.nodes[-1].outgoingEdges])


if __name__ == "__main__":
    pruningThreshold = float(sys.argv[1])
    lmScale = float(sys.argv[2])
    numWords = int(sys.argv[3])

    open('results.ctm', 'a').close()
    os.remove('results.ctm')
    open('confidenceMeasures.txt', 'a').close()
    os.remove('confidenceMeasures.txt')

    print("---------START DECODING---------")
    wg1 = WordGraph('lattice.1.htk.gz', 1.151, '_0000001151_0000014843', 'results.ctm', 'confidenceMeasures.txt', pruningThreshold, lmScale, 'log semiring')
    wg2 = WordGraph('lattice.2.htk.gz', 16.353 , '_0000016353_0000024761', 'results.ctm', 'confidenceMeasures.txt', pruningThreshold, lmScale, 'log semiring')
    wg3 = WordGraph('lattice.3.htk.gz', 24.761, '_0000024761_0000044466', 'results.ctm', 'confidenceMeasures.txt', pruningThreshold, lmScale, 'log semiring')
    wg4 = WordGraph('lattice.4.htk.gz', 44.466, '_0000044466_0000063151', 'results.ctm', 'confidenceMeasures.txt', pruningThreshold, lmScale, 'log semiring')
    wg5 = WordGraph('lattice.5.htk.gz', 63.151, '_0000063151_0000078481', 'results.ctm', 'confidenceMeasures.txt', pruningThreshold, lmScale, 'log semiring')
   
    print("Word Graph Density",(wg1.numEdges + wg2.numEdges + wg3.numEdges + wg4.numEdges + wg5.numEdges)/float(numWords))
    print("Pruning threshold", pruningThreshold)
    print("---------DONE----------")
