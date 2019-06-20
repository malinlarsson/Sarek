#! /usr/bin/env python

import argparse
import re
import sys
import gzip
import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime


def mkParser():
    parser = argparse.ArgumentParser(description = "merge variants from different callers and generates statistics")
    parser.add_argument("--tumorid", type = str, help="Tumor sample ID", required = True)
    parser.add_argument("--normalid", type=str, help="Normal sample ID", required=True)
    parser.add_argument("--mutect2vcf", type=str, help="MuTect2 VCF file", required=True)
    parser.add_argument("--strelkavcf", type=str, help="Strelka SNV VCF file", required=True)
    parser.add_argument("--strelkaindelvcf", type=str, help="Strelka indel VCF file", required=True)
    parser.add_argument("--genomeindex", type=str, help="Index of the used genome (generated by samtools faidx)", required=True)
    return parser.parse_args()


def mergeVCFs(tumorid, normalid,  mutect2vcf, strelkavcf, strelkaindelvcf, genomeindex):
    mutect2=parse_mutect2(mutect2vcf, tumorid, normalid)
    strelka=parse_strelka(strelkavcf, strelkaindelvcf)
    generate_output(mutect2, strelka, tumorid, normalid, genomeindex)
    plot_allele_freqs(mutect2, strelka, tumorid)


def plot_allele_freqs(mutect2, strelka, tumorid):
    #columns =  ['MuTect1','MuTect2', 'Strelka', 'M1M2I_M1','M1M2I_M2' 'M1SI_M1', 'M1SI_S','M2SI_M2', 'M2SI_S','M1M2SI_M1','M1M2SI_M2','M1M2SI_S' ]
    #columns =  ['MuTect1_singletons','MuTect2_singletons', 'Strelka_singletons', 'M1M2I', 'M1SI', 'M2SI','M1M2SI']
    columns =  ['MuTect2_singletons','Strelka_singletons','MuTect2_all','Strelka_all','MuTect2_Strelka']
    count = np.zeros((5), dtype=np.int)

    #allele_freq=np.empty(12)
    allele_freq=np.empty(5)
    #allele_freq[:] = numpy.NAN

    all_snvs=set(mutect2['snvs'].keys()+strelka['snvs'].keys())
    antal=0
    for pos in all_snvs:

        #print pos

        #this_variant=np.empty(12)
        this_variant=np.empty(5)
        this_variant[:]=-999
        vcfinfo = {}
        #Which caller(s) detected the variant?
        if pos in mutect2['snvs']:
            vcfinfo['mutect2']=mutect2['snvs'][pos]['ad']['tumor']
        if pos in strelka['snvs']:
            vcfinfo['strelka']=strelka['snvs'][pos]['ad']['tumor']

        #Singletons
        if 'mutect2' in vcfinfo.keys() and 'strelka' not in vcfinfo.keys():
            this_variant[0]=float(vcfinfo['mutect2'].split(",")[1])/(float(vcfinfo['mutect2'].split(",")[0])+float(vcfinfo['mutect2'].split(",")[1]))
            count[0]=count[0]+1
            #if this_variant[0]>1:
                #print this_variant[0]
                #print mutect2['snvs'][pos]['ad']['tumor']

        if 'mutect2' not in vcfinfo.keys() and 'strelka' in vcfinfo.keys():
            #print this_variant[0]
            #print vcfinfo['strelka']
            this_variant[1]=float(vcfinfo['strelka'].split(",")[1])/(float(vcfinfo['strelka'].split(",")[0])+float(vcfinfo['strelka'].split(",")[1]))
            count[1]=count[1]+1

        #All calls by callers
        if 'mutect2' in vcfinfo.keys():
            this_variant[2]=float(vcfinfo['mutect2'].split(",")[1])/(float(vcfinfo['mutect2'].split(",")[0])+float(vcfinfo['mutect2'].split(",")[1]))
            count[2]=count[2]+1
        if 'strelka' in vcfinfo.keys():
            this_variant[3]=float(vcfinfo['strelka'].split(",")[1])/(float(vcfinfo['strelka'].split(",")[0])+float(vcfinfo['strelka'].split(",")[1]))
            count[3]=count[3]+1

        #Intersection of two callers - allele frequencies calculated as mean of reported for callers
        if 'mutect2' in vcfinfo.keys() and 'strelka' in vcfinfo.keys():
            #this_variant[7]=float(vcfinfo['mutect2'].split(",")[1])/(float(vcfinfo['mutect2'].split(",")[0])+float(vcfinfo['mutect2'].split(",")[1]))
            #this_variant[8]=float(vcfinfo['strelka'].split(",")[1])/(float(vcfinfo['strelka'].split(",")[0])+float(vcfinfo['strelka'].split(",")[1]))
            this_variant[4]=(float(vcfinfo['mutect2'].split(",")[1])/(float(vcfinfo['mutect2'].split(",")[0])+float(vcfinfo['mutect2'].split(",")[1]))+float(vcfinfo['strelka'].split(",")[1])/(float(vcfinfo['strelka'].split(",")[0])+float(vcfinfo['strelka'].split(",")[1])))/2
            count[4]=count[4]+1


        allele_freq=np.vstack((allele_freq, this_variant))


    #Mask NaNs in allele_freq
    masked_allele_freq=np.ma.masked_equal(allele_freq,-999)
    allele_freqs_nonempty = [[y for y in row if y] for row in masked_allele_freq.T]

    #Create plots and print to PDF file
    numBoxes=5
    pp = PdfPages(tumorid+'_allele_freqs.pdf')
    fig, ax1 = plt.subplots(figsize=(7, 6))
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
    ax1.set_title('SNVs called in '+tumorid+'\n')
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
    print 'printed results to '+tumorid+'_allele_freqs.pdf'



def generate_output(mutect2, strelka, tumorid, normalid, genomeIndex):
    snv_file=tumorid+'.snvs.vcf'
    indel_file=tumorid+'.indels.vcf'
    avinput=tumorid+'.avinput'
    sf = open(snv_file, 'w')
    ai = open(avinput, 'w')
    inf = open(indel_file, 'w')

    #Writing snv file
    sf.write("%s\n" %("##fileformat=VCFv4.2"))
    sf.write("%s%s\n" %("##date=",str(datetime.now())))
    sf.write("%s%s\n" %("##source=",sys.argv[0]))
    sf.write("%s\n" %("##FILTER=<ID=CONCORDANT,Description=\"Called by both MuTect2 and Strelka)\""))
    sf.write("%s\n" %("##FILTER=<ID=DISCORDANT,Description=\"Only called by one caller\""))
    sf.write("%s\n" %("##INFO=<ID=M2,Number=.,Type=String,Description=\"Called by MuTect2\""))
    sf.write("%s\n" %("##INFO=<ID=S,Number=.,Type=String,Description=\"Called by Strelka\""))
    sf.write("%s\n" %("##FORMAT=<ID=ADM2,Number=.,Type=Integer,Description=\"Allelic depths reported by MuTect2 for the ref and alt alleles in the order listed\""))
    sf.write("%s\n" %("##FORMAT=<ID=ADS,Number=.,Type=Integer,Description=\"Allelic depths reported by Strelka for the ref and alt alleles in the order listed\""))
    sf.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" %('#CHROM', 'POS','ID', 'REF', 'ALT','QUAL', 'FILTER', 'INFO','FORMAT', tumorid, normalid))
    #All mutated snvs:
    all_snvs=set(mutect2['snvs'].keys()+strelka['snvs'].keys())
    antal=0
    sorted_pos=sort_positions(all_snvs, genomeIndex)
    for pos in sorted_pos:
        #for pos in all_snvs:
        vcfinfo = {}
        #Which caller(s) detected the variant?
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
                if c=='mutect2':
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
            if len(called_by)==2:
                filter="CONCORDANT"
            vcfinfolist=vcfinfo[called_by[0]].split('\t')
            baseinfo=vcfinfolist[0]+'\t'+vcfinfolist[1]+'\tNA\t'+vcfinfolist[2]+'\t'+vcfinfolist[3]+'\t'+'.'
            sf.write("%s\t%s\t%s\t%s\t%s\t%s\n" %(baseinfo,filter, callers, format, gf_tumor, gf_normal))
            ai.write("%s\n" %(vcfinfo[called_by[0]]))
        else:
            print "Conflict in ref and alt alleles between callers "
                  #+called_by+" at pos "+pos

    # Writing indel file
    inf.write("%s\n" % ("##fileformat=VCFv4.2"))
    inf.write("%s%s\n" % ("##date=", str(datetime.now())))
    inf.write("%s%s\n" % ("##source=", sys.argv[0]))
    inf.write("%s\n" % ("##FILTER=<ID=CONCORDANT,Description=\"Called by both MuTect2 and Strelka)\""))
    inf.write("%s\n" % ("##FILTER=<ID=DISCORDANT,Description=\"Only called by one caller\""))
    inf.write("%s\n" % ("##INFO=<ID=M2,Number=.,Type=String,Description=\"Called by MuTect2\""))
    inf.write("%s\n" % ("##INFO=<ID=S,Number=.,Type=String,Description=\"Called by Strelka\""))
    inf.write("%s\n" % (
        "##FORMAT=<ID=ADM2,Number=.,Type=Integer,Description=\"Allelic depths reported by MuTect2 for the ref and alt alleles in the order listed\""))
    inf.write("%s\n" % (
        "##FORMAT=<ID=ADS,Number=.,Type=Integer,Description=\"Allelic depths reported by Strelka for the ref and alt alleles in the order listed\""))
    inf.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
    '#CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO', 'FORMAT', tumorid, normalid))
    # All mutated snvs:
    all_indels = set(mutect2['indels'].keys() + strelka['indels'].keys())

    antal = 0
    d_alt = 0
    sorted_pos_indels = sort_positions(all_indels, genomeIndex)
    for pos in sorted_pos_indels:

        #Number of calls with different alt alleles:

        vcfinfo = {}
        # Which caller(s) detected the variant?
        if pos in mutect2['indels']:
            vcfinfo['mutect2'] = mutect2['indels'][pos]['info']
        if pos in strelka['indels']:
            vcfinfo['strelka'] = strelka['indels'][pos]['info']
        called_by = vcfinfo.keys()
        # Do we have the same basic info from all callers? Should be...
        if all(value == vcfinfo[called_by[0]] for value in vcfinfo.values()):
            format = ''
            gf_tumor = ''
            gf_normal = ''
            callers = ''
            for c in called_by:
                if c == 'mutect2':
                    callers = callers + 'M2;'
                    format = format + 'ADM2:'
                    gf_tumor = gf_tumor + mutect2['indels'][pos]['ad']['tumor'] + ':'
                    gf_normal = gf_normal + mutect2['indels'][pos]['ad']['normal'] + ':'
                elif c == 'strelka':
                    callers = callers + 'S;'
                    format = format + 'ADS:'
                    gf_tumor = gf_tumor + strelka['indels'][pos]['ad']['tumor'] + ':'
                    gf_normal = gf_normal + strelka['indels'][pos]['ad']['normal'] + ':'
            callers = callers[:-1]
            format = format[:-1]
            gf_tumor = gf_tumor[:-1]
            gf_normal = gf_normal[:-1]
            antal = antal + 1
            filter = "DISCORDANT"
            if len(called_by) == 2:
                filter = "CONCORDANT"
            vcfinfolist = vcfinfo[called_by[0]].split('\t')
            baseinfo = vcfinfolist[0] + '\t' + vcfinfolist[1] + '\tNA\t' + vcfinfolist[2] + '\t' + vcfinfolist[
                3] + '\t' + '.'
            inf.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (baseinfo, filter, callers, format, gf_tumor, gf_normal))
            ai.write("%s\n" % (vcfinfo[called_by[0]]))
        else:
            print "Conflict in ref and alt alleles between callers "
            d_alt = d_alt + 1
            print "mutect2 "+vcfinfo['mutect2']
            print "strelka "+vcfinfo['strelka']
            # +called_by+" at pos "+pos
    print "antal med conflict: "+str(d_alt)
    print "antal utan: "+str(antal)

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


def parse_mutect2(vcf, tumorid, normalid):
    snvs = {}
    indels = {}
    datacolumn = {}
    for line in gzip.open(vcf, 'r'):
        line=line.strip()
        # Extract column in vcf file for "TUMOR" and "NORMAL"
        if line.startswith("#CHROM"):
            info = line.split("\t")
            for col in range(9, len(info)):
                if info[col] in [tumorid, normalid]:
                    datacolumn[info[col]] = col
                else:
                    print "ERROR: sample ids other than "+tumorid+" or "+normalid+" detected in MuTect2 vcf"
                    break
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
            filter10=re.compile('PASS')
            f10=filter10.search(line)
            #if not (f1 or f2 or f3 or f4 or f5 or f6 or f7 or f8 or f9):
            if (f10):
                info=line.split("\t")
                pos=info[0]+'_'+info[1]
                vcfinfo=info[0]+'\t'+info[1]+'\t'+info[3]+'\t'+info[4]
                ad_tumor=info[datacolumn[tumorid]].split(":")[1]
                ad_normal=info[datacolumn[normalid]].split(":")[1]
                ref=info[3]
                alt=info[4]
                alt_alleles = alt.split(",")
                if len(alt_alleles) == 1:
                    #Indels
                    if len(ref)>1 or len(alt)>1:

                        #print "this is an indel!"
                        #print vcfinfo
                        #print ad_tumor
                        #print ad_normal
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
                #else:
                    #print "WARNING: MuTect2 variant with multiple alternative alleles detected; skipped and not used in merged callset:"
                    #print line
    return {'indels':indels,'snvs':snvs}


def parse_mutect1(vcf, tumorid, normalid):
    snvs = {}
    datacolumn = {}
    for line in gzip.open(vcf, 'r'):
        line=line.strip()
        # Extract column in vcf file for each sample
        if line.startswith("#CHROM"):
            info = line.split("\t")
            for col in range(9, len(info)):
                if info[col] in [tumorid, normalid]:
                    datacolumn[info[col]]=col
                else:
                    print "ERROR: sample ids other than "+tumorid+" or "+normalid+" detected in MuTect1 vcf"
                    break
        if not line.startswith("#"):
            filter1 = re.compile('REJECT')
            f1 = filter1.search(line)
            if not (f1):
                info=line.split("\t")
                pos = info[0] + '_' + info[1]
                vcfinfo = info[0] + '\t' + info[1] + '\t' + info[3] + '\t' + info[4]
                ad_tumor = info[datacolumn[tumorid]].split(":")[1]
                ad_normal = info[datacolumn[normalid]].split(":")[1]
                alt=info[4]
                alt_alleles=alt.split(",")
                if len(alt_alleles) == 1:
                    snvs[pos] = {}
                    snvs[pos]['info']=vcfinfo
                    snvs[pos]['ad'] = {}
                    snvs[pos]['ad']['tumor']=ad_tumor
                    snvs[pos]['ad']['normal']=ad_normal
                else:
                    print "WARNING: MuTect1 variant with multiple alternative alleles detected; skipped and not used in merged callset."
                    print line
    return {'snvs':snvs}

def parse_strelka(vcf, indelvcf):
    #Please see this post for parsing strelka SNVs: https://github.com/Illumina/strelka/tree/master/docs/userGuide
    snvs = {}
    datacolumn = {}
    for line in gzip.open(vcf, 'r'):
        line=line.strip()
        # Extract column in vcf file for "TUMOR" and "NORMAL"
        if line.startswith("#CHROM"):
            info = line.split("\t")
            for col in range(9, len(info)):
                if info[col] in ['TUMOR', 'NORMAL']:
                    datacolumn[info[col]] = col
                else:
                    print "ERROR: Strelka VCF file does not contain column for TUMOR or NORMAL"
                    break
        if not line.startswith("#"):

            filter1 = re.compile('LowEVS')
            f1 = filter1.search(line)
            filter2 = re.compile('LowDepth')
            f2 = filter2.search(line)
            if not (f1 or f2):
                info=line.split("\t")
                pos=info[0]+'_'+info[1]
                ref=info[3]
                alt=info[4]
                ad_normal = {}
                ad_tumor = {}
                #Using tiers 1 data
                ad_normal['A']=int(info[datacolumn['NORMAL']].split(":")[4].split(",")[0])
                ad_normal['C']=int(info[datacolumn['NORMAL']].split(":")[5].split(",")[0])
                ad_normal['G']=int(info[datacolumn['NORMAL']].split(":")[6].split(",")[0])
                ad_normal['T']=int(info[datacolumn['NORMAL']].split(":")[7].split(",")[0])
                ad_tumor['A'] = int(info[datacolumn['TUMOR']].split(":")[4].split(",")[0])
                ad_tumor['C'] = int(info[datacolumn['TUMOR']].split(":")[5].split(",")[0])
                ad_tumor['G'] = int(info[datacolumn['TUMOR']].split(":")[6].split(",")[0])
                ad_tumor['T'] = int(info[datacolumn['TUMOR']].split(":")[7].split(",")[0])
                snvs[pos] = {}
                snvs[pos]['ad'] = {}
                # If several alternative alleles are detected in the tumor, report the most highly abundant one and print a warning message.
                alt_allele=''
                alt_depth_tumor = 0
                alt_alt_normal = 0
                alt_alleles=alt.split(",")
                for allele in alt_alleles:
                    if ad_tumor[allele] > alt_depth_tumor:
                        alt_depth_tumor=ad_tumor[allele]
                        alt_depth_normal=ad_normal[allele]
                        alt_allele=allele
                if len(alt) > 1:
                    print "WARNING: Strelka variant with multiple alternative alleles detected. Reporting the alternative allele with highest read count:"
                    print line

                vcfinfo = info[0] + '\t' + info[1] + '\t' + info[3] + '\t' + alt_allele
                snvs[pos]['info'] = vcfinfo
                snvs[pos]['ad']['tumor']=str(ad_tumor[ref])+','+str(alt_depth_tumor)
                snvs[pos]['ad']['normal']=str(ad_normal[ref])+','+str(alt_depth_normal)


    indels = {}
    datacolumn = {}
    for line in gzip.open(indelvcf, 'r'):
        line=line.strip()
        # Extract column in vcf file for "TUMOR" and "NORMAL"
        if line.startswith("#CHROM"):
            info = line.split("\t")
            for col in range(9, len(info)):
                if info[col] in ['TUMOR', 'NORMAL']:
                    datacolumn[info[col]] = col
                else:
                    print "ERROR: Strelka VCF file does not contain column for TUMOR or NORMAL"
                    break
        if not line.startswith("#"):

            filter1 = re.compile('LowEVS')
            f1 = filter1.search(line)
            filter2 = re.compile('LowDepth')
            f2 = filter2.search(line)
            if not (f1 or f2):
                info=line.split("\t")
                pos=info[0]+'_'+info[1]
                ref=info[3]
                alt=info[4]
                #Using tiers 1 data
                refCounts_normal=int(info[datacolumn['NORMAL']].split(":")[3].split(",")[0])
                altCounts_normal = int(info[datacolumn['NORMAL']].split(":")[4].split(",")[0])
                refCounts_tumor = int(info[datacolumn['TUMOR']].split(":")[3].split(",")[0])
                altCounts_tumor = int(info[datacolumn['TUMOR']].split(":")[4].split(",")[0])

                indels[pos] = {}
                indels[pos]['ad'] = {}
                # If several alternative alleles are detected in the tumor, report the most highly abundant one and print a warning message.

                alt_alleles=alt.split(",")

                if len(alt_alleles)>1:
                    print "WARNING: Strelka indel with multiple alternative alleles detected."
                    print line

                vcfinfo = info[0] + '\t' + info[1] + '\t' + info[3] + '\t' + alt
                indels[pos]['info'] = vcfinfo
                indels[pos]['ad']['tumor']=str(refCounts_tumor)+','+str(altCounts_tumor)
                indels[pos]['ad']['normal']=str(refCounts_normal)+','+str(altCounts_normal)

    return {'indels':indels,'snvs':snvs}



def main():
    args = mkParser()
    mergeVCFs(args.tumorid, args.normalid, args.mutect2vcf, args.strelkavcf, args.strelkaindelvcf, args.genomeindex)

main()

