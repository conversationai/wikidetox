language=en
dumpdate=20180701
cloudBucket=wikidetox-viz-dataflow
cloudProject=wikidetox-viz

python dataflow_postprocess.py --input gs://${cloudBucket}/wikiconv_v2/${language}-${dumpdate}/cleaned_results/wikiconv-${language}-${dumpdate}-* --setup_file ./setup.py --output gs://${cloudBucket}/wikiconv_v2/${language}-${dumpdate}/final_results/wikiconv-${language}-${dumpdate}- --jobname=${language}${dumpdate} --project ${cloudProject} --bucket ${cloudBucket} || exit 1
