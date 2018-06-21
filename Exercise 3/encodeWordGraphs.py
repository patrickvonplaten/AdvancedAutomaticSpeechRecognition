#!/usr/bin/env python3
import gzip
import math
import os
from operator import attrgetter

class Node(object):

    def __init__(self, index, time):
        self.index = index
        self.time = time
        self.incomingEdges = []
        self.outgoingEdges = []
        self.forwardProb = None
        self.backwardProb = None

    def addToIncomingEdges(self, edge):
        self.incomingEdges.append(edge)

    def addToOutgoingEdges(self, edge):
        self.outgoingEdges.append(edge)

    def setForwardProb(self, p):
        self.forwardProb = p

    def setBackwardProb(self, p):
        self.backwardProb = p


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

    def setNegativeLogPosteriorProb(self, posteriorProb):
        self.posteriorProb = posteriorProb

class WordGraph(object):

    def __init__(self, latticeFilePath, startTime, code, resultFilePath):
        self.nodes = []
        self.edges = []
        self.encodedResults = []
        self.lmScale = None 
        self.numNodes = None
        self.numEdges = None
        self.fullPathProb = None
        self.startTime = float(startTime)
        self.endTime = None
        self.code = code
        self.resultFilePath = resultFilePath
        self.parseLattice(latticeFilePath)
        self.runForwardBackwardAlgorithm()
        self.encodeWordGraph()
        self.writeResultsToCTMFile()

    def parseLattice(self, latticeFilePath):
        with gzip.open(latticeFilePath, 'rb') as file:
            for line in file:
                line = self.convertToRegString(line)
                lineType = self.getLineType(line)
                if(lineType == 'edge'):
                    edge = self.parseEdge(line)
                    self.nodes[edge.nodeFrom].addToOutgoingEdges(edge)
                    self.nodes[edge.nodeTo].addToIncomingEdges(edge)
                    self.edges.append(edge)
                elif(lineType == 'node'):
                     self.nodes.append(self.parseNode(line))
                elif(lineType == 'lmScale'):
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

        for edge in self.edges:
            edge.setNegativeLogPosteriorProb(self.nodes[edge.nodeFrom].forwardProb + edge.weight + self.nodes[edge.nodeTo].backwardProb - self.fullPathProb)

    def calculateProbability(self, nodes, probabilityType, nameOfEdgesList, nodeType):
        for node in nodes[1:]:
            value = float('inf') 
            max = 0
            for edge in getattr(node, nameOfEdgesList):
                edgeNode = self.nodes[getattr(edge, nodeType)]
                value = self.getValueSum(value, getattr(edgeNode, probabilityType) + edge.weight)     
                if(value > max):
                    max = value
                assert value > 0, "negative log probability cannot be < 0" 
            setattr(node, probabilityType, value)

    def getValueSum(self, value, summedProb):
        if value == float('inf'):
            return summedProb 
        else:
            return - (math.log(1 + math.exp(-abs(summedProb - value))) - min(summedProb, value))
    
    def encodeWordGraph(self):
        node = self.nodes[0]
        while(len(node.outgoingEdges) is not 0):
            timeStart = node.time
            bestEdge = min(node.outgoingEdges, key=attrgetter('posteriorProb'))
            node = self.nodes[bestEdge.nodeTo]
            timeEnd = node.time + self.startTime
            timeDiff = timeEnd - timeStart
            self.encodedResults.append(((bestEdge.word[1:-1]), round(timeEnd, 3), round(timeDiff, 3)))
        self.endTime = timeEnd

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
    open('results.ctm', 'a').close()
    os.remove('results.ctm')
    wg = WordGraph('lattice.1.htk.gz', 0, '_0000001151_0000014843', 'results.ctm')
