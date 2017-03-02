#! /usr/bin/env python

import re
import sys

import matplotlib

matplotlib.use('pdf')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

if len(sys.argv)<5:
    print "Usage: %s sample_name MuTect1_vcf MuTect2_vcf Strelka_vcf genomeIndex\n" %sys.argv[0]
    sys.exit(0)


def main():
    sample = sys.argv[1]
    mutect1_vcf = sys.argv[2]
    mutect2_vcf = sys.argv[3]
    strelka_vcf= sys.argv[4]
    genomeIndex=sys.argv[5]
    mutect2=parse_mutect2(mutect2_vcf)
    mutect1=parse_mutect1(mutect1_vcf)
    strelka=parse_strelka_snvs(strelka_vcf)
    generate_output(mutect1, mutect2, strelka, sample, genomeIndex)
    plot_allele_freqs(mutect1, mutect2, strelka, sample)


def plot_allele_freqs(mutect1, mutect2, strelka, sample):
    #columns =  ['MuTect1','MuTect2', 'Strelka', 'M1M2I_M1','M1M2I_M2' 'M1SI_M1', 'M1SI_S','M2SI_M2', 'M2SI_S','M1M2SI_M1','M1M2SI_M2','M1M2SI_S' ]
    #columns =  ['MuTect1_singletons','MuTect2_singletons', 'Strelka_singletons', 'M1M2I', 'M1SI', 'M2SI','M1M2SI']
    columns =  ['MuTect1_singletons','MuTect2_singletons','Strelka_singletons','MuTect1_all','MuTect2_all','Strelka_all','MuTect1_MuTect2','MuTect1_Strelka','MuTect2_Strelka','MuTect1_MuTect2_Strelka']
    count = np.zeros((10), dtype=np.int)

    #allele_freq=np.empty(12)
    allele_freq=np.empty(10)
    #allele_freq[:] = numpy.NAN

    all_snvs=set(mutect1['snvs'].keys()+mutect2['snvs'].keys()+strelka['snvs'].keys())
    antal=0
    for pos in all_snvs:

        #this_variant=np.empty(12)
        this_variant=np.empty(10)
        this_variant[:]=-999
        vcfinfo = {}
        #Which caller(s) detected the variant?
        if pos in mutect1['snvs']:
            vcfinfo['mutect1']=mutect1['snvs'][pos]['ad']['tumor']
        if pos in mutect2['snvs']:
            vcfinfo['mutect2']=mutect2['snvs'][pos]['ad']['tumor']
        if pos in strelka['snvs']:
            vcfinfo['strelka']=strelka['snvs'][pos]['ad']['tumor']

        #Singletons
        if 'mutect1' in vcfinfo.keys() and 'mutect2' not in vcfinfo.keys() and 'strelka' not in vcfinfo.keys():
            this_variant[0]=float(vcfinfo['mutect1'].split(",")[1])/(float(vcfinfo['mutect1'].split(",")[0])+float(vcfinfo['mutect1'].split(",")[1]))
            count[0]=count[0]+1

        if 'mutect1' not in vcfinfo.keys() and 'mutect2' in vcfinfo.keys() and 'strelka' not in vcfinfo.keys():
            this_variant[1]=float(vcfinfo['mutect2'].split(",")[1])/(float(vcfinfo['mutect2'].split(",")[0])+float(vcfinfo['mutect2'].split(",")[1]))
            count[1]=count[1]+1
            if this_variant[1]>1:
                print this_variant[1]
                print mutect2['snvs'][pos]['ad']['tumor']

        if 'mutect1' not in vcfinfo.keys() and 'mutect2' not in vcfinfo.keys() and 'strelka' in vcfinfo.keys():
            this_variant[2]=float(vcfinfo['strelka'].split(",")[1])/(float(vcfinfo['strelka'].split(",")[0])+float(vcfinfo['strelka'].split(",")[1]))
            count[2]=count[2]+1

        #All calles by callers
        if 'mutect1' in vcfinfo.keys():
            this_variant[3]=float(vcfinfo['mutect1'].split(",")[1])/(float(vcfinfo['mutect1'].split(",")[0])+float(vcfinfo['mutect1'].split(",")[1]))
            count[3]=count[3]+1
        if 'mutect2' in vcfinfo.keys():
            this_variant[4]=float(vcfinfo['mutect2'].split(",")[1])/(float(vcfinfo['mutect2'].split(",")[0])+float(vcfinfo['mutect2'].split(",")[1]))
            count[4]=count[4]+1
        if 'strelka' in vcfinfo.keys():
            this_variant[5]=float(vcfinfo['strelka'].split(",")[1])/(float(vcfinfo['strelka'].split(",")[0])+float(vcfinfo['strelka'].split(",")[1]))
            count[5]=count[5]+1

        #Intersection of two callers - allele frequencies calculated as mean of reported for callers
        if 'mutect1' in vcfinfo.keys() and 'mutect2' in vcfinfo.keys():
            #this_variant[3]=float(vcfinfo['mutect1'].split(",")[1])/(float(vcfinfo['mutect1'].split(",")[0])+float(vcfinfo['mutect1'].split(",")[1]))
            #this_variant[4]=float(vcfinfo['mutect2'].split(",")[1])/(float(vcfinfo['mutect2'].split(",")[0])+float(vcfinfo['mutect2'].split(",")[1]))
            this_variant[6]=(float(vcfinfo['mutect1'].split(",")[1])/(float(vcfinfo['mutect1'].split(",")[0])+float(vcfinfo['mutect1'].split(",")[1])) + float(vcfinfo['mutect2'].split(",")[1])/(float(vcfinfo['mutect2'].split(",")[0])+float(vcfinfo['mutect2'].split(",")[1])))/2
            count[6]=count[6]+1
        if 'mutect1' in vcfinfo.keys() and 'strelka' in vcfinfo.keys():
            #this_variant[5]=float(vcfinfo['mutect1'].split(",")[1])/(float(vcfinfo['mutect1'].split(",")[0])+float(vcfinfo['mutect1'].split(",")[1]))
            #this_variant[6]=float(vcfinfo['strelka'].split(",")[1])/(float(vcfinfo['strelka'].split(",")[0])+float(vcfinfo['strelka'].split(",")[1]))
            this_variant[7]=(float(vcfinfo['mutect1'].split(",")[1])/(float(vcfinfo['mutect1'].split(",")[0])+float(vcfinfo['mutect1'].split(",")[1])) + float(vcfinfo['strelka'].split(",")[1])/(float(vcfinfo['strelka'].split(",")[0])+float(vcfinfo['strelka'].split(",")[1])))/2
            count[7]=count[7]+1
        if 'mutect2' in vcfinfo.keys() and 'strelka' in vcfinfo.keys():
            #this_variant[7]=float(vcfinfo['mutect2'].split(",")[1])/(float(vcfinfo['mutect2'].split(",")[0])+float(vcfinfo['mutect2'].split(",")[1]))
            #this_variant[8]=float(vcfinfo['strelka'].split(",")[1])/(float(vcfinfo['strelka'].split(",")[0])+float(vcfinfo['strelka'].split(",")[1]))
            this_variant[8]=(float(vcfinfo['mutect2'].split(",")[1])/(float(vcfinfo['mutect2'].split(",")[0])+float(vcfinfo['mutect2'].split(",")[1]))+float(vcfinfo['strelka'].split(",")[1])/(float(vcfinfo['strelka'].split(",")[0])+float(vcfinfo['strelka'].split(",")[1])))/2
            count[8]=count[8]+1
        #Intersection of three callers - allele frequencies calculated as mean of reported for callers
        if 'mutect1' in vcfinfo.keys() and 'mutect2' in vcfinfo.keys() and 'strelka' in vcfinfo.keys():
            #this_variant[9]=float(vcfinfo['mutect1'].split(",")[1])/(float(vcfinfo['mutect1'].split(",")[0])+float(vcfinfo['mutect1'].split(",")[1]))
            #this_variant[10]=float(vcfinfo['mutect2'].split(",")[1])/(float(vcfinfo['mutect2'].split(",")[0])+float(vcfinfo['mutect2'].split(",")[1]))
            #this_variant[11]=float(vcfinfo['strelka'].split(",")[1])/(float(vcfinfo['strelka'].split(",")[0])+float(vcfinfo['strelka'].split(",")[1]))
            this_variant[9]=(float(vcfinfo['mutect1'].split(",")[1])/(float(vcfinfo['mutect1'].split(",")[0])+float(vcfinfo['mutect1'].split(",")[1])) + float(vcfinfo['mutect2'].split(",")[1])/(float(vcfinfo['mutect2'].split(",")[0])+float(vcfinfo['mutect2'].split(",")[1])) + float(vcfinfo['strelka'].split(",")[1])/(float(vcfinfo['strelka'].split(",")[0])+float(vcfinfo['strelka'].split(",")[1])))/3
            count[9]=count[9]+1

        allele_freq=np.vstack((allele_freq, this_variant))


    #Mask NaNs in allele_freq
    masked_allele_freq=np.ma.masked_equal(allele_freq,-999)
    allele_freqs_nonempty = [[y for y in row if y] for row in masked_allele_freq.T]

    #Create plots and print to PDF file
    numBoxes=10
    pp = PdfPages(sample+'_allele_freqs.pdf')
    fig, ax1 = plt.subplots(figsize=(10, 6))
    plt.subplots_adjust(left=0.075, right=0.95, top=0.9, bottom=0.25)
    x=range(1, len(columns)+1)
    bp = plt.boxplot(allele_freqs_nonempty, notch=0, sym='+', vert=1, whis=1.5)
    plt.setp(bp['boxes'], color='black')
    plt.setp(bp['whiskers'], color='black')
    plt.setp(bp['fliers'], color='red', marker='+')
    ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey',
               alpha=0.5)
    # Hide these grid behind plot objects
    ax1.set_axisbelow(True)
    ax1.set_title('SNVs called in '+sample+'\n')
    ax1.set_xlabel('Call set')
    ax1.set_ylabel('Alternative allele frequency')
    # Set the axes ranges and axes labels
    ax1.set_xlim(0.5, numBoxes + 0.5)
    top = 1.2
    bottom = 0
    ax1.set_ylim(bottom, top)
    xtickNames = plt.setp(ax1, xticklabels=columns)
    plt.setp(xtickNames, rotation=45, fontsize=8)
    #Print counts and medians above the boxes
    for tick, label in zip(x, count):
        ax1.text(tick, 1.1, 'n = '+str(label),horizontalalignment='center', size='x-small')
    median_values=[]
    for medline in bp['medians']:
        median_values.append(str(round(medline.get_ydata()[0],2)))
    for tick, label in zip(x, median_values):
        ax1.text(tick, 1, 'm = '+str(label),horizontalalignment='center', size='x-small')
    plt.savefig(pp, format='pdf')
    pp.close()
    print 'printed results to '+sample+'_allele_freqs.pdf'



def generate_output(mutect1, mutect2, strelka, sample, genomeIndex):
    snv_file=sample+'.snvs.vcf'
    avinput=sample+'.avinput'
    sf = open(snv_file, 'w')
    ai = open(avinput, 'w')
    sf.write("%s\n" %("##fileformat=VCFv4.2"))
    sf.write("%s%s\n" %("##date=",str(datetime.now())))
    sf.write("%s%s\n" %("##source=",sys.argv[0]))
    sf.write("%s\n" %("##FILTER=<ID=CONCORDANT,Description=\"Called by all three callers (MuTect1, MuTect2 and Strelka)\""))
    sf.write("%s\n" %("##FILTER=<ID=DISCORDANT,Description=\"NOT called by all three callers\""))
    sf.write("%s\n" %("##INFO=<ID=M1,Number=.,Type=String,Description=\"Called by MuTect1\""))
    sf.write("%s\n" %("##INFO=<ID=M2,Number=.,Type=String,Description=\"Called by MuTect2\""))
    sf.write("%s\n" %("##INFO=<ID=S,Number=.,Type=String,Description=\"Called by Strelka\""))
    sf.write("%s\n" %("##FORMAT=<ID=ADM1,Number=.,Type=Integer,Description=\"Allelic depths reported by MuTect1 for the ref and alt alleles in the order listed\""))
    sf.write("%s\n" %("##FORMAT=<ID=ADM2,Number=.,Type=Integer,Description=\"Allelic depths reported by MuTect2 for the ref and alt alleles in the order listed\""))
    sf.write("%s\n" %("##FORMAT=<ID=ADS,Number=.,Type=Integer,Description=\"Allelic depths reported by Strelka for the ref and alt alleles in the order listed\""))
    sf.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" %('#CHROM', 'POS','ID', 'REF', 'ALT','QUAL', 'FILTER', 'INFO','FORMAT', sample+'_tumor', sample+'_normal'))
    #All mutated snvs:
    all_snvs=set(mutect1['snvs'].keys()+mutect2['snvs'].keys()+strelka['snvs'].keys())
    antal=0
    sorted_pos=sort_positions(all_snvs, genomeIndex)
    for pos in sorted_pos:
        #for pos in all_snvs:
        vcfinfo = {}
        #Which caller(s) detected the variant?
        if pos in mutect1['snvs']:
            vcfinfo['mutect1']=mutect1['snvs'][pos]['info']
        if pos in mutect2['snvs']:
            vcfinfo['mutect2']=mutect2['snvs'][pos]['info']
        if pos in strelka['snvs']:
            vcfinfo['strelka']=strelka['snvs'][pos]['info']
        called_by=vcfinfo.keys()
        #Do we have the same basic info from all callers? Should be...
        if all(value == vcfinfo[called_by[0]] for value in vcfinfo.values()):
            format=''
            gf_tumor=''
            gf_normal=''
            callers=''
            for c in called_by:
                if c=='mutect1':
                    callers=callers+'M1;'
                    format=format+'ADM1:'
                    gf_tumor=gf_tumor+mutect1['snvs'][pos]['ad']['tumor']+':'
                    gf_normal=gf_normal+mutect1['snvs'][pos]['ad']['normal']+':'
                elif c=='mutect2':
                    callers=callers+'M2;'
                    format=format+'ADM2:'
                    gf_tumor=gf_tumor+mutect2['snvs'][pos]['ad']['tumor']+':'
                    gf_normal=gf_normal+mutect2['snvs'][pos]['ad']['normal']+':'
                elif c=='strelka':
                    callers=callers+'S;'
                    format=format+'ADS:'
                    gf_tumor=gf_tumor+strelka['snvs'][pos]['ad']['tumor']+':'
                    gf_normal=gf_normal+strelka['snvs'][pos]['ad']['normal']+':'
            callers = callers[:-1]
            format = format[:-1]
            gf_tumor = gf_tumor[:-1]
            gf_normal = gf_normal[:-1]
            antal = antal+1
            filter="DISCORDANT"
            if len(called_by)==3:
                filter="CONCORDANT"
            vcfinfolist=vcfinfo[called_by[0]].split('\t')
            baseinfo=vcfinfolist[0]+'\t'+vcfinfolist[1]+'\tNA\t'+vcfinfolist[2]+'\t'+vcfinfolist[3]+'\t'+'.'
            sf.write("%s\t%s\t%s\t%s\t%s\t%s\n" %(baseinfo,filter, callers, format, gf_tumor, gf_normal))
            ai.write("%s\n" %(vcfinfo[called_by[0]]))
        else:
            print "Conflict in ref and alt alleles between callers "+called_by+" at pos "+pos


def sort_positions(positions, genomeIndex):
    CHROMOSOMES = []
    selected = []
    sorted = []
    for line in open(genomeIndex, 'r'):
        line = line.strip()
        info = line.split("\t")
        CHROMOSOMES.append(info[0])
        selected.append([])
    for pos in positions:
        chr_pos=pos.split("_")
        if chr_pos[0] in CHROMOSOMES:
            selected[CHROMOSOMES.index(chr_pos[0])].append(int(chr_pos[1]))
    for chr in CHROMOSOMES:
        selected[CHROMOSOMES.index(chr)].sort()
        for pos in selected[CHROMOSOMES.index(chr)]:
            sorted.append(chr+'_'+str(pos))
    return sorted


def parse_mutect2(vcf):
    snvs = {}
    indels = {}
    for line in open(vcf, 'r'):
        line=line.strip()
        if not line.startswith("#"):
            filter1=re.compile('alt_allele_in_normal')
            filter2=re.compile('clustered_events')
            filter3=re.compile('germline_risk')
            filter4=re.compile('homologous_mapping_event')
            filter5=re.compile('multi_event_alt_allele_in_normal')
            filter6=re.compile('panel_of_normals')
            filter7=re.compile('str_contraction')
            filter8=re.compile('t_lod_fstar')
            filter9=re.compile('triallelic_site')
            f1=filter1.search(line)
            f2=filter2.search(line)
            f3=filter3.search(line)
            f4=filter4.search(line)
            f5=filter5.search(line)
            f6=filter6.search(line)
            f7=filter7.search(line)
            f8=filter8.search(line)
            f9=filter9.search(line)
            if not (f1 or f2 or f3 or f4 or f5 or f6 or f7 or f8 or f9):
                info=line.split("\t")
                pos=info[0]+'_'+info[1]
                vcfinfo=info[0]+'\t'+info[1]+'\t'+info[3]+'\t'+info[4]
                ad_tumor=info[9].split(":")[1]
                ad_normal=info[10].split(":")[1]
                ref=info[3]
                alt=info[4]
                #Indels
                if len(ref)>1 or len(alt)>1:
                    indels[pos] = {}
                    indels[pos]['info']=vcfinfo
                    indels[pos]['ad'] = {}
                    indels[pos]['ad']['tumor']=ad_tumor
                    indels[pos]['ad']['normal']=ad_normal
                #snvs
                else:
                    snvs[pos] = {}
                    snvs[pos]['info']=vcfinfo
                    snvs[pos]['ad'] = {}
                    snvs[pos]['ad']['tumor']=ad_tumor
                    snvs[pos]['ad']['normal']=ad_normal
    return {'indels':indels,'snvs':snvs}


def parse_mutect1(vcf):
    snvs = {}
    for line in open(vcf, 'r'):
        line=line.strip()
        if not line.startswith("#"):
            filter1=re.compile('REJECT')
            f1=filter1.search(line)
            if not (f1):
                info=line.split("\t")
                pos=info[0]+'_'+info[1]
                vcfinfo=info[0]+'\t'+info[1]+'\t'+info[3]+'\t'+info[4]
                if info[4] in ['A', 'C', 'G', 'T']:
                    ad_tumor=info[9].split(":")[1]
                    ad_normal=info[10].split(":")[1]
                    snvs[pos] = {}
                    snvs[pos]['info']=vcfinfo
                    snvs[pos]['ad'] = {}
                    snvs[pos]['ad']['tumor']=ad_tumor
                    snvs[pos]['ad']['normal']=ad_normal
                else:
                    print "WARNING: MuTect1 variant skipped because it has multiple alternative alleles:"
                    print line
    return {'snvs':snvs}

def parse_strelka_snvs(vcf):
    snvs = {}
    for line in open(vcf, 'r'):
        line=line.strip()
        if not line.startswith("#"):
            info=line.split("\t")
            pos=info[0]+'_'+info[1]
            vcfinfo=info[0]+'\t'+info[1]+'\t'+info[3]+'\t'+info[4]
            ref=info[3]
            alt=info[4]
            #Check if SNP has one alternative allele:
            #if alt in ['A','C','G','T']:
            ad_normal = {}
            ad_tumor = {}
            #Using tiers 2 data
            ad_tumor['A']=int(info[10].split(":")[4].split(",")[1])
            ad_tumor['C']=int(info[10].split(":")[5].split(",")[1])
            ad_tumor['G']=int(info[10].split(":")[6].split(",")[1])
            ad_tumor['T']=int(info[10].split(":")[7].split(",")[1])
            ad_normal['A']=int(info[9].split(":")[4].split(",")[1])
            ad_normal['C']=int(info[9].split(":")[5].split(",")[1])
            ad_normal['G']=int(info[9].split(":")[6].split(",")[1])
            ad_normal['T']=int(info[9].split(":")[7].split(",")[1])
            snvs[pos] = {}
            snvs[pos]['info']=vcfinfo
            snvs[pos]['ad'] = {}


            #alt_allele_index={"A":4,"C":5,"G":6,"T":7}

            major_alt_tumor = 0
            major_alt_normal = 0
            alt_alleles=alt.split(",")
            for allele in alt_alleles:
                if ad_tumor[allele] > major_alt_tumor:
                    major_alt_tumor=ad_tumor[allele]
                    major_alt_normal=ad_normal[allele]
            if len(alt) > 1:
                print "WARNING: Strelka variant with multiple alternative alleles detected. Using the alternative allele with highest read count:"
                print line
            snvs[pos]['ad']['tumor']=str(ad_tumor[ref])+','+str(major_alt_tumor)
            snvs[pos]['ad']['normal']=str(ad_normal[ref])+','+str(major_alt_normal)
            #else:
            #    print "WARNING: Strelka variant skipped because it has multiple alternative alleles:"
            #    print line

    return {'snvs':snvs}

main()