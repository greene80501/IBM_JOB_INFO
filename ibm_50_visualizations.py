
#!/usr/bin/env python3
from __future__ import annotations
import argparse,re
from collections import Counter
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation, TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.manifold import TSNE
from sklearn.metrics.pairwise import cosine_similarity
from wordcloud import WordCloud
import textstat
import umap

STATE_ABBR_TO_NAME={'AL':'Alabama','AK':'Alaska','AZ':'Arizona','AR':'Arkansas','CA':'California','CO':'Colorado','CT':'Connecticut','DE':'Delaware','FL':'Florida','GA':'Georgia','HI':'Hawaii','ID':'Idaho','IL':'Illinois','IN':'Indiana','IA':'Iowa','KS':'Kansas','KY':'Kentucky','LA':'Louisiana','ME':'Maine','MD':'Maryland','MA':'Massachusetts','MI':'Michigan','MN':'Minnesota','MS':'Mississippi','MO':'Missouri','MT':'Montana','NE':'Nebraska','NV':'Nevada','NH':'New Hampshire','NJ':'New Jersey','NM':'New Mexico','NY':'New York','NC':'North Carolina','ND':'North Dakota','OH':'Ohio','OK':'Oklahoma','OR':'Oregon','PA':'Pennsylvania','RI':'Rhode Island','SC':'South Carolina','SD':'South Dakota','TN':'Tennessee','TX':'Texas','UT':'Utah','VT':'Vermont','VA':'Virginia','WA':'Washington','WV':'West Virginia','WI':'Wisconsin','WY':'Wyoming','DC':'District of Columbia'}
STATE_CENTROIDS={'TX':(31,-99),'NY':(43,-75),'IL':(40,-89),'GA':(33,-83.5),'LA':(31,-92),'NC':(35.5,-79),'DC':(38.9,-77),'CA':(37,-119),'AZ':(34,-111),'VA':(37.5,-78.5),'WA':(47.5,-120.5),'SC':(33.8,-80.9),'MA':(42.3,-71.8),'MI':(44.5,-85.5),'WV':(38.6,-80.6),'MN':(46,-94)}
CITY_TO_STATE={'ARMONK':'NY','AUSTIN':'TX','BATON ROUGE':'LA','BELLEVUE':'WA','BUFFALO':'NY','COLUMBIA':'SC','CAMBRIDGE':'MA','CHICAGO':'IL','HOPEWELL JUNCTION':'NY','HERNDON':'VA','LANSING':'MI','MONROE':'LA','NEW YORK':'NY','POUGHKEEPSIE':'NY','RESEARCH TRIANGLE PARK':'NC','ROCHESTER':'MN','ROCKET CENTER':'WV','SAN JOSE':'CA','TUCSON':'AZ','UNIVERSITY PARK':'IL','WASHINGTON':'DC','YORKTOWN HEIGHTS':'NY','ATLANTA':'GA','DALLAS':'TX','HOUSTON':'TX','DURHAM':'NC','BROOKHAVEN':'GA'}
CITY_STATE_COORDS={('AUSTIN','TX'):(30.2672,-97.7431),('ATLANTA','GA'):(33.749,-84.388),('CHICAGO','IL'):(41.8781,-87.6298),('DALLAS','TX'):(32.7767,-96.797),('HOUSTON','TX'):(29.7604,-95.3698),('DURHAM','NC'):(35.994,-78.8986),('NEW YORK','NY'):(40.7128,-74.006),('BROOKHAVEN','GA'):(33.8651,-84.3366),('BATON ROUGE','LA'):(30.4515,-91.1871),('POUGHKEEPSIE','NY'):(41.7004,-73.921),('BUFFALO','NY'):(42.8864,-78.8784),('WASHINGTON','DC'):(38.9072,-77.0369),('ROCHESTER','MN'):(44.0121,-92.4802),('SAN JOSE','CA'):(37.3382,-121.8863),('TUCSON','AZ'):(32.2226,-110.9747),('UNIVERSITY PARK','IL'):(41.4464,-87.6848),('COLUMBIA','SC'):(34.0007,-81.0348),('MONROE','LA'):(32.5093,-92.1193),('HOPEWELL JUNCTION','NY'):(41.562,-73.8065),('YORKTOWN HEIGHTS','NY'):(41.2706,-73.7774),('ARMONK','NY'):(41.1265,-73.714),('HERNDON','VA'):(38.9696,-77.3861),('CAMBRIDGE','MA'):(42.3736,-71.1097),('BELLEVUE','WA'):(47.6101,-122.2015),('ROCKET CENTER','WV'):(39.5612,-78.7998),('LANSING','MI'):(42.7325,-84.5555),('RESEARCH TRIANGLE PARK','NC'):(35.9049,-78.873)}
SKILL_TERMS=['python','java','sql','spark','hadoop','aws','azure','ibm cloud','machine learning','data science','ai','genai','nlp','react','node','kubernetes','docker','salesforce','sap','workday','security','devops','agile','tableau','snowflake','postgres','db2','mongodb']
LOCATION_PATTERN=re.compile(r"\b([A-Z][A-Za-z .&\-/]{1,40}),\s*([A-Z]{2})\b")
STOPWORDS=set('a an and are as at be by for from has have in into is it of on or that the this to was were will with your you'.split())

def clean_text(s): return re.sub(r'\s+',' ',str(s or '').replace('\u2019',"'").replace('\u2018',"'")).strip()
def normalize_title(s):
    s=re.sub(r'\b20\d{2}\b','',str(s or '').lower())
    s=re.sub(r'[^a-z0-9 ]+',' ',s)
    return re.sub(r'\s+',' ',s).strip()

def infer_states_and_cities(row):
    states,cities=set(),set(); text=' '.join(str(row.get(c,'') or '') for c in ['title','official_title','location_summary','intro','responsibilities','skills_required','skills_preferred','extra_content'])
    for city,st in LOCATION_PATTERN.findall(text):
        cu=city.strip().upper()
        if st in STATE_ABBR_TO_NAME and len(cu)<=40 and ' WORKING IN ' not in cu: states.add(st); cities.add((cu,st))
    loc=str(row.get('location_summary','') or '').strip()
    if loc and loc!='Multiple Cities':
        city=loc.split(',')[0].strip().upper()
        if city in CITY_TO_STATE: st=CITY_TO_STATE[city]; states.add(st); cities.add((city,st))
    if re.search(r'Washington,\s*DC',text,flags=re.I): states.add('DC'); cities.add(('WASHINGTON','DC'))
    return sorted(states),sorted(cities)

def prep(df):
    df=df.copy(); df['posted_at']=pd.to_datetime(df['posted_at'],errors='coerce'); df['salary_min']=pd.to_numeric(df['salary_min'],errors='coerce'); df['salary_max']=pd.to_numeric(df['salary_max'],errors='coerce')
    df['salary_mid']=(df['salary_min']+df['salary_max'])/2; df['salary_spread']=df['salary_max']-df['salary_min']; mx=df['posted_at'].max(); df['posting_age_days']=(mx-df['posted_at']).dt.days
    df['role_type']=np.where(df['career_level'].str.contains('intern',case=False,na=False)|df['title'].str.contains('intern|co-op|apprentice',case=False,na=False),'Intern/Co-op/Apprentice','Full-time/Other')
    df['work_type']=df['work_type'].fillna('Unknown'); df['category']=df['category'].fillna('Unknown'); df['department']=df['department'].fillna('Unknown')
    df['travel_norm']=df['travel'].fillna('Unknown').str.lower().str.extract(r'(0%|up to \d+%|unknown)')[0].fillna('other')
    df['all_text']=(df['intro'].fillna('')+' '+df['responsibilities'].fillna('')+' '+df['skills_required'].fillna('')+' '+df['skills_preferred'].fillna('')).map(clean_text)
    df['description_chars']=df['all_text'].str.len(); df['description_words']=df['all_text'].str.split().str.len(); df['title_norm']=df['title'].map(normalize_title)
    df['commission_bool']=df['commission_role'].astype(str).str.lower().isin(['true','1','yes']); df['visa_language']=df['all_text'].str.contains(re.compile(r'visa|sponsorship|work authorization|authorized to work',re.I))
    inf=df.apply(infer_states_and_cities,axis=1); df['states_inferred']=inf.map(lambda x:x[0]); df['cities_inferred']=inf.map(lambda x:x[1]); df['state_count']=df['states_inferred'].map(len)
    def add_coords(lst):
        out=[]
        for city,st in lst:
            lat,lon=CITY_STATE_COORDS.get((city,st),STATE_CENTROIDS.get(st,(np.nan,np.nan)))
            if not np.isnan(lat) and not np.isnan(lon): out.append((city,st,lat,lon))
        return out
    df['city_points']=df['cities_inferred'].map(add_coords)
    return df

def explode_states(df):
    x=df[['id','category','career_level','employment_type','work_type','salary_min','salary_max','salary_mid','salary_spread','posted_at','posting_age_days','role_type','travel_norm','commission_bool','visa_language','edu_required','edu_preferred','title','title_norm','all_text','description_chars','description_words','states_inferred']].explode('states_inferred')
    x=x[x['states_inferred'].notna()&(x['states_inferred']!='')].copy(); return x.rename(columns={'states_inferred':'state'})

def explode_cities(df):
    rows=[]
    for _,r in df.iterrows():
        for city,st,lat,lon in r['city_points']: rows.append({'id':r['id'],'city':city.title(),'state':st,'lat':lat,'lon':lon,'category':r['category'],'role_type':r['role_type'],'work_type':r['work_type']})
    return pd.DataFrame(rows)

def save_plotly(fig,path): fig.write_html(str(path),include_plotlyjs='cdn')
def do_all(df,out):
    out.mkdir(parents=True,exist_ok=True); sns.set_theme(style='whitegrid'); manifest=[]; st=explode_states(df); ct=explode_cities(df)
    s1=st.groupby('state',as_index=False).agg(job_count=('id','nunique'))
    save_plotly(px.choropleth(s1,locations='state',locationmode='USA-states',color='job_count',scope='usa',color_continuous_scale='Blues',title='1. US choropleth: job counts by state'),out/'01_us_choropleth_state_jobs.html'); s1.to_csv(out/'01_jobs_by_state.csv',index=False); manifest.append((1,'US choropleth map','01_us_choropleth_state_jobs.html'))
    c2=ct.groupby(['city','state','lat','lon'],as_index=False).agg(job_count=('id','nunique')).sort_values('job_count',ascending=False)
    save_plotly(px.scatter_geo(c2,lat='lat',lon='lon',size='job_count',color='job_count',hover_name='city',hover_data={'state':True,'job_count':True},scope='usa',title='2. US city bubble map'),out/'02_city_bubble_map.html'); c2.to_csv(out/'02_city_counts.csv',index=False); manifest.append((2,'US city bubble map','02_city_bubble_map.html'))
    if not c2.empty:
        plt.figure(figsize=(10,6)); plt.hexbin(c2['lon'],c2['lat'],C=c2['job_count'],reduce_C_function=np.sum,gridsize=20,cmap='YlOrRd',mincnt=1); plt.xlim(-125,-66); plt.ylim(24,50); plt.title('3. Job concentration hotspots (hexbin)'); plt.xlabel('Longitude'); plt.ylabel('Latitude'); plt.colorbar(label='Jobs'); plt.tight_layout(); plt.savefig(out/'03_hexbin_hotspots.png',dpi=180); plt.close()
    manifest.append((3,'Hexbin density hotspots','03_hexbin_hotspots.png'))
    plt.figure(figsize=(12,5))
    for i,rt in enumerate(['Intern/Co-op/Apprentice','Full-time/Other'],start=1):
        sub=ct[ct['id'].isin(df[df['role_type']==rt]['id'])]; ax=plt.subplot(1,2,i)
        if not sub.empty: ax.hexbin(sub['lon'],sub['lat'],gridsize=18,cmap='Blues',mincnt=1)
        ax.set_xlim(-125,-66); ax.set_ylim(24,50); ax.set_title(rt); ax.set_xlabel('Lon'); ax.set_ylabel('Lat')
    plt.suptitle('4. Internship vs Full-time density'); plt.tight_layout(); plt.savefig(out/'04_side_by_side_role_type_density.png',dpi=180); plt.close(); manifest.append((4,'Internship vs full-time density map','04_side_by_side_role_type_density.png'))
    wts=df['work_type'].dropna().value_counts().head(4).index.tolist(); fig,axes=plt.subplots(2,2,figsize=(12,8))
    for ax,wt in zip(axes.flat,wts):
        sub=ct[ct['id'].isin(df[df['work_type']==wt]['id'])]
        if not sub.empty: ax.scatter(sub['lon'],sub['lat'],s=20,alpha=0.7)
        ax.set_xlim(-125,-66); ax.set_ylim(24,50); ax.set_title(wt)
    plt.suptitle('5. Faceted US maps by work type'); plt.tight_layout(); plt.savefig(out/'05_work_type_faceted_maps.png',dpi=180); plt.close(); manifest.append((5,'Faceted maps by work type','05_work_type_faceted_maps.png'))
    h6=st.pivot_table(index='state',columns='category',values='id',aggfunc='nunique',fill_value=0); plt.figure(figsize=(14,8)); sns.heatmap(h6,cmap='viridis'); plt.title('6. State-by-category heatmap'); plt.tight_layout(); plt.savefig(out/'06_state_category_heatmap.png',dpi=180); plt.close(); h6.to_csv(out/'06_state_category_matrix.csv'); manifest.append((6,'State by category heatmap','06_state_category_heatmap.png'))
    c7=c2.sort_values('job_count',ascending=False).head(25); plt.figure(figsize=(12,8)); sns.barplot(data=c7,y='city',x='job_count',hue='state',dodge=False); plt.title('7. Top 25 cities by job count'); plt.tight_layout(); plt.savefig(out/'07_top25_cities_bar.png',dpi=180); plt.close(); manifest.append((7,'Top 25 cities bar','07_top25_cities_bar.png'))
    t8=df.groupby(['category','department'],as_index=False).agg(job_count=('id','nunique')); save_plotly(px.treemap(t8,path=['category','department'],values='job_count',title='8. Treemap: category and department'),out/'08_treemap_category_department.html'); manifest.append((8,'Treemap category/department','08_treemap_category_department.html'))
    t9=df.groupby(['category','career_level','employment_type'],as_index=False).agg(job_count=('id','nunique')); save_plotly(px.sunburst(t9,path=['category','career_level','employment_type'],values='job_count',title='9. Sunburst category → level → employment'),out/'09_sunburst_cat_level_employment.html'); manifest.append((9,'Sunburst category-career level-employment','09_sunburst_cat_level_employment.html'))
    s10=st.groupby(['state','category','work_type'],as_index=False).agg(job_count=('id','nunique')); a=sorted(s10['state'].unique().tolist()); b=sorted(s10['category'].unique().tolist()); c=sorted(s10['work_type'].unique().tolist()); nodes=a+b+c; ix={n:i for i,n in enumerate(nodes)}; src=[]; tgt=[]; val=[]
    for _,r in s10.groupby(['state','category'],as_index=False)['job_count'].sum().iterrows(): src.append(ix[r['state']]); tgt.append(ix[r['category']]); val.append(r['job_count'])
    for _,r in s10.groupby(['category','work_type'],as_index=False)['job_count'].sum().iterrows(): src.append(ix[r['category']]); tgt.append(ix[r['work_type']]); val.append(r['job_count'])
    fig=go.Figure(data=[go.Sankey(node=dict(label=nodes),link=dict(source=src,target=tgt,value=val))]); fig.update_layout(title='10. Sankey: state → category → work arrangement'); save_plotly(fig,out/'10_sankey_state_category_worktype.html'); manifest.append((10,'Sankey state-category-work','10_sankey_state_category_worktype.html'))
    t11=st.groupby(['state','work_type'],as_index=False).agg(job_count=('id','nunique')); p11=t11.pivot_table(index='state',columns='work_type',values='job_count',fill_value=0); p11.plot(kind='bar',stacked=True,figsize=(12,6),colormap='tab20'); plt.title('11. State split by work arrangement'); plt.tight_layout(); plt.savefig(out/'11_state_worktype_stacked_bar.png',dpi=180); plt.close(); manifest.append((11,'Stacked bar state by work arrangement','11_state_worktype_stacked_bar.png'))
    t12=st.groupby('state',as_index=False).agg(avg_min=('salary_min','mean'),avg_max=('salary_max','mean')); plt.figure(figsize=(12,6)); plt.scatter(t12['state'],t12['avg_min'],label='Avg min salary'); plt.scatter(t12['state'],t12['avg_max'],label='Avg max salary'); plt.xticks(rotation=90); plt.legend(); plt.title('12. Average salary range by state'); plt.tight_layout(); plt.savefig(out/'12_dotplot_salary_range_by_state.png',dpi=180); plt.close(); manifest.append((12,'Dot plot average salary range by state','12_dotplot_salary_range_by_state.png'))
    t13=df.groupby('category',as_index=False).agg(avg_min=('salary_min','mean'),avg_max=('salary_max','mean')).sort_values('avg_max'); plt.figure(figsize=(12,7))
    for i,r in t13.reset_index(drop=True).iterrows(): plt.plot([r['avg_min'],r['avg_max']],[i,i],color='gray'); plt.scatter(r['avg_min'],i,color='blue',s=30); plt.scatter(r['avg_max'],i,color='red',s=30)
    plt.yticks(range(len(t13)),t13['category']); plt.title('13. Dumbbell: min vs max salary by category'); plt.xlabel('Salary'); plt.tight_layout(); plt.savefig(out/'13_dumbbell_salary_by_category.png',dpi=180); plt.close(); manifest.append((13,'Dumbbell salary by category','13_dumbbell_salary_by_category.png'))
    plt.figure(figsize=(12,7)); sns.boxplot(data=df,x='category',y='salary_mid'); plt.xticks(rotation=60,ha='right'); plt.title('14. Salary distribution per category'); plt.tight_layout(); plt.savefig(out/'14_boxplot_salary_by_category.png',dpi=180); plt.close(); manifest.append((14,'Boxplot salary per category','14_boxplot_salary_by_category.png'))
    top=st['state'].value_counts().head(8).index.tolist(); t15=st[st['state'].isin(top)]; plt.figure(figsize=(12,7)); sns.violinplot(data=t15,x='state',y='salary_mid'); plt.title('15. Salary violin by top states'); plt.tight_layout(); plt.savefig(out/'15_violin_salary_top_states.png',dpi=180); plt.close(); manifest.append((15,'Violin salary by top states','15_violin_salary_top_states.png'))
    plt.figure(figsize=(10,6)); sns.scatterplot(data=df,x='posting_age_days',y='salary_mid',hue='category',alpha=0.7); plt.title('16. Salary midpoint vs posting age'); plt.tight_layout(); plt.savefig(out/'16_scatter_salary_vs_posting_age.png',dpi=180); plt.close(); manifest.append((16,'Scatter salary midpoint vs posting age','16_scatter_salary_vs_posting_age.png'))
    day_df = df.assign(date=df['posted_at'].dt.date)
    week_df = df.assign(week=df['posted_at'].dt.to_period('W').astype(str))
    t17d = day_df.groupby('date', as_index=False).agg(job_count=('id', 'nunique'))
    t17w = week_df.groupby('week', as_index=False).agg(job_count=('id', 'nunique'))
    plt.figure(figsize=(12,5)); plt.plot(pd.to_datetime(t17d['date']),t17d['job_count'],marker='o'); plt.title('17. Jobs posted per day'); plt.tight_layout(); plt.savefig(out/'17_timeseries_jobs_per_day.png',dpi=180); plt.close()
    plt.figure(figsize=(12,5)); plt.plot(t17w['week'],t17w['job_count'],marker='o'); plt.xticks(rotation=60,ha='right'); plt.title('17. Jobs posted per week'); plt.tight_layout(); plt.savefig(out/'17_timeseries_jobs_per_week.png',dpi=180); plt.close(); t17d.to_csv(out/'17_jobs_per_day.csv',index=False); t17w.to_csv(out/'17_jobs_per_week.csv',index=False); manifest.append((17,'Time series per day/week','17_timeseries_jobs_per_day.png'))
    cal=df[['posted_at','id']].dropna().copy(); cal['dow']=cal['posted_at'].dt.weekday; cal['week']=cal['posted_at'].dt.isocalendar().week.astype(int); p18=cal.pivot_table(index='dow',columns='week',values='id',aggfunc='count',fill_value=0)
    plt.figure(figsize=(14,4)); sns.heatmap(p18,cmap='YlGnBu'); plt.title('18. Calendar heatmap posting volume'); plt.tight_layout(); plt.savefig(out/'18_calendar_heatmap.png',dpi=180); plt.close(); manifest.append((18,'Calendar heatmap','18_calendar_heatmap.png'))
    return manifest,st,ct
def do_more(df,out,manifest,st,ct):
    t17d=pd.read_csv(out/'17_jobs_per_day.csv')
    t19=t17d.copy(); t19['cum_jobs']=t19['job_count'].cumsum(); plt.figure(figsize=(10,5)); plt.plot(pd.to_datetime(t19['date']),t19['cum_jobs']); plt.title('19. Cumulative postings curve'); plt.tight_layout(); plt.savefig(out/'19_cumulative_postings_curve.png',dpi=180); plt.close(); manifest.append((19,'Cumulative postings curve','19_cumulative_postings_curve.png'))
    cats20=df['category'].value_counts().head(6).index.tolist(); plt.figure(figsize=(12,8))
    for c in cats20:
        vals=df[df['category']==c]['posted_at'].dropna().map(datetime.toordinal)
        if len(vals)>1: sns.kdeplot(vals,fill=True,alpha=.35,linewidth=1,label=c)
    plt.title('20. Ridgeline-like KDE of posting dates by category'); plt.legend(); plt.tight_layout(); plt.savefig(out/'20_ridgeline_posting_dates.png',dpi=180); plt.close(); manifest.append((20,'Ridgeline posting dates by category','20_ridgeline_posting_dates.png'))
    t21=df.groupby(['role_type','travel_norm'],as_index=False).agg(job_count=('id','nunique')); plt.figure(figsize=(12,6)); sns.barplot(data=t21,x='travel_norm',y='job_count',hue='role_type'); plt.title('21. Travel requirement phrases grouped by role type'); plt.tight_layout(); plt.savefig(out/'21_hist_travel_by_role_type.png',dpi=180); plt.close(); manifest.append((21,'Histogram travel phrases by role type','21_hist_travel_by_role_type.png'))
    vals=df['commission_bool'].value_counts(); plt.figure(figsize=(6,6)); plt.pie(vals.values,labels=['Non-commission' if not k else 'Commission' for k in vals.index],autopct='%1.1f%%',wedgeprops={'width':0.4}); plt.title('22. Commission vs non-commission donut'); plt.tight_layout(); plt.savefig(out/'22_donut_commission.png',dpi=180); plt.close(); manifest.append((22,'Donut commission vs non-commission','22_donut_commission.png'))
    h23=df.pivot_table(index='category',columns='contract_type',values='id',aggfunc='nunique',fill_value=0); plt.figure(figsize=(12,7)); sns.heatmap(h23,cmap='magma'); plt.title('23. Category vs contract type'); plt.tight_layout(); plt.savefig(out/'23_heatmap_category_contract.png',dpi=180); plt.close(); manifest.append((23,'Heatmap category vs contract type','23_heatmap_category_contract.png'))
    ed=(df['edu_required'].fillna('')+' | '+df['edu_preferred'].fillna('')).str.lower(); df['edu_bin']=np.select([ed.str.contains('master'),ed.str.contains('bachelor'),ed.str.contains('high school|ged')],['Masters','Bachelors','HighSchool/GED'],default='Other/Unspecified')
    h24=df.pivot_table(index='category',columns='edu_bin',values='id',aggfunc='nunique',fill_value=0); plt.figure(figsize=(12,7)); sns.heatmap(h24,cmap='crest'); plt.title('24. Category vs education requirement'); plt.tight_layout(); plt.savefig(out/'24_heatmap_category_education.png',dpi=180); plt.close(); manifest.append((24,'Heatmap category vs education','24_heatmap_category_education.png'))
    t25=df.groupby(['category','visa_language'],as_index=False).agg(job_count=('id','nunique')); p25=t25.pivot_table(index='category',columns='visa_language',values='job_count',fill_value=0); p25.plot(kind='bar',stacked=True,figsize=(12,6)); plt.title('25. Visa language by category'); plt.tight_layout(); plt.savefig(out/'25_stacked_visa_language.png',dpi=180); plt.close(); manifest.append((25,'Stacked bar visa language','25_stacked_visa_language.png'))
    df[['id','title','salary_spread']].sort_values('salary_spread',ascending=False).head(20).to_csv(out/'26_table_top_salary_spread_roles.csv',index=False); manifest.append((26,'Table widest salary spread','26_table_top_salary_spread_roles.csv'))
    df.groupby('title_norm',as_index=False).agg(freq=('id','count')).sort_values('freq',ascending=False).head(40).to_csv(out/'27_table_frequent_normalized_titles.csv',index=False); manifest.append((27,'Table frequent normalized titles','27_table_frequent_normalized_titles.csv'))
    wc=WordCloud(width=1400,height=700,background_color='white',stopwords=STOPWORDS).generate(' '.join(df['all_text'].dropna().tolist())); plt.figure(figsize=(14,7)); plt.imshow(wc,interpolation='bilinear'); plt.axis('off'); plt.title('28. Word cloud responsibilities/description'); plt.tight_layout(); plt.savefig(out/'28_wordcloud_responsibilities.png',dpi=180); plt.close(); manifest.append((28,'Word cloud','28_wordcloud_responsibilities.png'))
    vec2=CountVectorizer(stop_words='english',ngram_range=(2,2),min_df=2); X2=vec2.fit_transform(df['all_text']); bi_counts=np.asarray(X2.sum(axis=0)).ravel(); bi_terms=np.array(vec2.get_feature_names_out()); top_idx=bi_counts.argsort()[::-1][:40]
    G=nx.Graph();
    for i in top_idx: a,b=bi_terms[i].split(' ',1); G.add_edge(a,b,weight=float(bi_counts[i]))
    plt.figure(figsize=(12,10)); pos=nx.spring_layout(G,seed=42); nx.draw_networkx(G,pos,node_size=600,font_size=8,width=[G[u][v]['weight']/20 for u,v in G.edges()]); plt.title('29. Bigram network graph'); plt.axis('off'); plt.tight_layout(); plt.savefig(out/'29_bigram_network.png',dpi=180); plt.close(); manifest.append((29,'Bigram network graph','29_bigram_network.png'))
    vec3=CountVectorizer(stop_words='english',ngram_range=(3,3),min_df=2); X3=vec3.fit_transform(df['all_text']); tri_counts=np.asarray(X3.sum(axis=0)).ravel(); tri_terms=np.array(vec3.get_feature_names_out()); t30=pd.DataFrame({'trigram':tri_terms,'count':tri_counts}).sort_values('count',ascending=False).head(25)
    plt.figure(figsize=(12,8)); sns.barplot(data=t30,y='trigram',x='count',color='steelblue'); plt.title('30. Top trigrams'); plt.tight_layout(); plt.savefig(out/'30_trigram_bar.png',dpi=180); plt.close(); t30.to_csv(out/'30_top_trigrams.csv',index=False); manifest.append((30,'Trigram bar chart','30_trigram_bar.png'))
    def terms_in_text(t): tl=t.lower(); return [s for s in SKILL_TERMS if s in tl]
    df['skill_terms']=df['all_text'].map(terms_in_text); pair_counts=Counter()
    for skills in df['skill_terms']:
        uniq=sorted(set(skills))
        for i in range(len(uniq)):
            for j in range(i+1,len(uniq)): pair_counts[(uniq[i],uniq[j])]+=1
    Gs=nx.Graph();
    for (a,b),w in pair_counts.items():
        if w>=2: Gs.add_edge(a,b,weight=w)
    plt.figure(figsize=(12,10)); pos=nx.spring_layout(Gs,seed=11); nx.draw_networkx(Gs,pos,node_size=1000,font_size=8,width=[Gs[u][v]['weight']/2 for u,v in Gs.edges()],node_color='lightgreen'); plt.title('31. Skill co-occurrence network'); plt.axis('off'); plt.tight_layout(); plt.savefig(out/'31_skill_cooccurrence_network.png',dpi=180); plt.close(); manifest.append((31,'Skill co-occurrence network','31_skill_cooccurrence_network.png'))
    rows=[]
    for _,r in df.iterrows():
        for s in set(r['skill_terms']): rows.append({'category':r['category'],'skill':s,'id':r['id']})
    sf=pd.DataFrame(rows)
    if len(sf):
        h32=sf.pivot_table(index='skill',columns='category',values='id',aggfunc='nunique',fill_value=0); plt.figure(figsize=(14,10)); sns.heatmap(h32,cmap='rocket_r'); plt.title('32. Skill frequency by category'); plt.tight_layout(); plt.savefig(out/'32_skill_category_heatmap.png',dpi=180); plt.close()
    else: (out/'32_skill_category_heatmap.png').write_text('No skill data',encoding='utf-8')
    manifest.append((32,'Skill frequency heatmap by category','32_skill_category_heatmap.png'))
    top_cats=df['category'].value_counts().head(4).index.tolist(); top_skills=sf['skill'].value_counts().head(8).index.tolist() if len(sf) else SKILL_TERMS[:8]; radar=[]
    for c in top_cats: txt=' '.join(df[df['category']==c]['all_text'].tolist()).lower(); radar.append([txt.count(sk) for sk in top_skills])
    angles=np.linspace(0,2*np.pi,len(top_skills),endpoint=False).tolist(); angles+=angles[:1]; fig=plt.figure(figsize=(8,8)); ax=plt.subplot(111,polar=True)
    for i,c in enumerate(top_cats): vals=radar[i]+[radar[i][0]]; ax.plot(angles,vals,label=c)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(top_skills); ax.set_title('33. Skill profile radar by top categories'); ax.legend(loc='upper right',bbox_to_anchor=(1.35,1.15)); plt.tight_layout(); plt.savefig(out/'33_radar_skill_profiles.png',dpi=180); plt.close(); manifest.append((33,'Radar skill profiles','33_radar_skill_profiles.png'))
    vec_lda=CountVectorizer(stop_words='english',min_df=2,max_df=.9); X_lda=vec_lda.fit_transform(df['all_text']); lda=LatentDirichletAllocation(n_components=6,random_state=42); lda.fit(X_lda); terms=np.array(vec_lda.get_feature_names_out()); rows=[]
    for k,comp in enumerate(lda.components_):
        for rank,t in enumerate(terms[comp.argsort()[::-1][:12]],start=1): rows.append({'topic':k,'rank':rank,'term':t})
    t34=pd.DataFrame(rows); t34.to_csv(out/'34_lda_topics_terms.csv',index=False); plt.figure(figsize=(12,8))
    for k in range(6):
        sub=t34[t34['topic']==k]; plt.scatter([k]*len(sub),range(len(sub)),s=50)
        for j,term in enumerate(sub['term']): plt.text(k+.05,j,term,fontsize=8)
    plt.title('34. LDA topic terms'); plt.yticks([]); plt.tight_layout(); plt.savefig(out/'34_lda_topic_visualization.png',dpi=180); plt.close(); manifest.append((34,'LDA topic model visualization','34_lda_topic_visualization.png'))
    tfidf=TfidfVectorizer(stop_words='english',min_df=2,max_features=4000); X=tfidf.fit_transform(df['all_text']); svd=TruncatedSVD(n_components=min(100,X.shape[1]-1),random_state=42); emb=svd.fit_transform(X); k35=min(8,max(3,len(df)//20)); km=KMeans(n_clusters=k35,random_state=42,n_init=20)
    df['cluster35']=km.fit_predict(emb); vocab=np.array(tfidf.get_feature_names_out()); rows=[]
    for c in range(k35): idx=np.argsort(km.cluster_centers_[c])[::-1][:10]; rows.append({'cluster':c,'top_terms':', '.join(vocab[idx])})
    pd.DataFrame(rows).to_csv(out/'35_bertopic_like_cluster_terms.csv',index=False); plt.figure(figsize=(10,6)); sns.countplot(data=df,x='cluster35',hue='category'); plt.title('35. BERTopic-style embedding clusters'); plt.tight_layout(); plt.savefig(out/'35_bertopic_like_clusters.png',dpi=180); plt.close(); manifest.append((35,'BERTopic/embedding-like clusters','35_bertopic_like_clusters.png'))
    return manifest,st,ct,emb
def finish_all(df,out,manifest,st,ct,emb):
    reducer=umap.UMAP(random_state=42); um=reducer.fit_transform(emb); df['umap_x']=um[:,0]; df['umap_y']=um[:,1]
    plt.figure(figsize=(10,7)); sns.scatterplot(data=df,x='umap_x',y='umap_y',hue='category',s=50,alpha=.8); plt.title('36. UMAP of job descriptions'); plt.tight_layout(); plt.savefig(out/'36_umap_scatter_category.png',dpi=180); plt.close(); manifest.append((36,'UMAP scatter','36_umap_scatter_category.png'))
    def infer_seniority(t):
        tl=str(t).lower()
        if 'senior' in tl: return 'Senior'
        if 'associate' in tl or 'entry' in tl: return 'Entry/Associate'
        if 'intern' in tl or 'co-op' in tl or 'apprentice' in tl: return 'Intern/Co-op/Apprentice'
        return 'Other'
    df['seniority']=df['title'].map(infer_seniority); ts=TSNE(n_components=2,random_state=42,init='pca',perplexity=max(5,min(30,len(df)//4))).fit_transform(emb); df['tsne_x']=ts[:,0]; df['tsne_y']=ts[:,1]
    plt.figure(figsize=(10,7)); sns.scatterplot(data=df,x='tsne_x',y='tsne_y',hue='seniority',s=50,alpha=.8); plt.title('37. t-SNE embeddings by inferred seniority'); plt.tight_layout(); plt.savefig(out/'37_tsne_seniority.png',dpi=180); plt.close(); manifest.append((37,'t-SNE embeddings by seniority','37_tsne_seniority.png'))
    sim=cosine_similarity(emb); n=min(60,sim.shape[0]); idx=np.linspace(0,sim.shape[0]-1,n).astype(int); ss=sim[np.ix_(idx,idx)]; plt.figure(figsize=(10,8)); sns.heatmap(ss,cmap='coolwarm',center=.2); plt.title('38. Embedding similarity matrix (sample)'); plt.tight_layout(); plt.savefig(out/'38_similarity_matrix_heatmap.png',dpi=180); plt.close(); manifest.append((38,'Embedding similarity matrix','38_similarity_matrix_heatmap.png'))
    G=nx.Graph(); keep=min(40,len(df)); sk=cosine_similarity(emb[:keep])
    for i in range(keep): G.add_node(i,label=str(df.iloc[i]['title'])[:30])
    for i in range(keep):
        for j in np.argsort(sk[i])[::-1][1:4]: G.add_edge(i,j,weight=float(sk[i,j]))
    plt.figure(figsize=(12,10)); pos=nx.spring_layout(G,seed=42); nx.draw_networkx(G,pos,with_labels=False,node_size=250,alpha=.8); plt.title('39. Nearest-neighbor role similarity graph'); plt.axis('off'); plt.tight_layout(); plt.savefig(out/'39_nearest_neighbor_graph.png',dpi=180); plt.close(); manifest.append((39,'Nearest-neighbor explorer graph','39_nearest_neighbor_graph.png'))
    s40a=st.merge(df[['id','cluster35']],on='id',how='left').groupby(['cluster35','state'],as_index=False).agg(job_count=('id','nunique')); p40a=s40a.pivot_table(index='cluster35',columns='state',values='job_count',fill_value=0); p40a.plot(kind='bar',stacked=True,figsize=(12,6),colormap='tab20b'); plt.title('40a. Cluster composition by state'); plt.tight_layout(); plt.savefig(out/'40a_cluster_composition_state.png',dpi=180); plt.close()
    s40b=df.groupby(['cluster35','category'],as_index=False).agg(job_count=('id','nunique')); p40b=s40b.pivot_table(index='cluster35',columns='category',values='job_count',fill_value=0); p40b.plot(kind='bar',stacked=True,figsize=(12,6),colormap='tab20c'); plt.title('40b. Cluster composition by category'); plt.tight_layout(); plt.savefig(out/'40b_cluster_composition_category.png',dpi=180); plt.close(); manifest.append((40,'Cluster composition charts','40a_cluster_composition_state.png'))
    pos_words={'innovative','growth','learn','collaborate','success','opportunity','excellent','strong','improve','benefit'}; neg_words={'challenging','risk','problem','difficult','critical','complex'}
    def sent_score(t):
        words=re.findall(r'[a-z]+',str(t).lower());
        if not words: return 0.0
        p=sum(w in pos_words for w in words); n=sum(w in neg_words for w in words); return (p-n)/max(1,len(words))
    df['sentiment_score']=df['all_text'].map(sent_score); plt.figure(figsize=(12,7)); sns.boxplot(data=df,x='category',y='sentiment_score'); plt.xticks(rotation=60,ha='right'); plt.title('41. Sentiment score by category (lexicon approx)'); plt.tight_layout(); plt.savefig(out/'41_sentiment_by_category.png',dpi=180); plt.close(); manifest.append((41,'Sentiment distribution by category','41_sentiment_by_category.png'))
    df['readability_flesch']=df['all_text'].map(lambda t:textstat.flesch_reading_ease(str(t)[:10000]) if str(t) else np.nan); plt.figure(figsize=(12,7)); sns.boxplot(data=df,x='category',y='readability_flesch'); plt.xticks(rotation=60,ha='right'); plt.title('42. Flesch readability by category'); plt.tight_layout(); plt.savefig(out/'42_readability_by_category.png',dpi=180); plt.close(); manifest.append((42,'Readability comparison','42_readability_by_category.png'))
    plt.figure(figsize=(12,6)); sns.violinplot(data=df,x='category',y='description_words'); plt.xticks(rotation=60,ha='right'); plt.title('43. Description length (words) by category'); plt.tight_layout(); plt.savefig(out/'43_description_length_by_category.png',dpi=180); plt.close(); manifest.append((43,'Description length distribution','43_description_length_by_category.png'))
    ne=ct.groupby(['city','state','lat','lon'],as_index=False).agg(freq=('id','count')); save_plotly(px.scatter_geo(ne,lat='lat',lon='lon',size='freq',color='state',hover_name='city',scope='usa',title='44. Named-entity city/state map'),out/'44_named_entity_city_state_map.html'); manifest.append((44,'Named-entity map','44_named_entity_city_state_map.html'))
    amb=[]
    for _,r in df.iterrows():
        loc=str(r.get('location_summary','') or '')
        if loc.endswith(', US'):
            city=loc.split(',')[0].strip().upper()
            if city not in CITY_TO_STATE: amb.append({'id':r['id'],'title':r['title'],'location_summary':loc,'reason':'US city not mapped'})
        if r['state_count']==0: amb.append({'id':r['id'],'title':r['title'],'location_summary':loc,'reason':'no inferred state'})
    pd.DataFrame(amb).drop_duplicates().to_csv(out/'45_ambiguous_locations_table.csv',index=False); manifest.append((45,'Unresolved location cleanup table','45_ambiguous_locations_table.csv'))
    m46=ct.groupby(['city','state'],as_index=False).agg(job_count=('id','nunique')); city_nodes=m46['city'].tolist(); state_nodes=sorted(m46['state'].unique().tolist()); nodes=city_nodes+state_nodes; idx={n:i for i,n in enumerate(nodes)}
    fig=go.Figure(data=[go.Sankey(node=dict(label=nodes),link=dict(source=[idx[c] for c in m46['city']],target=[idx[s] for s in m46['state']],value=m46['job_count'].tolist()))]); fig.update_layout(title='46. City-to-state flow (chord-like Sankey)'); save_plotly(fig,out/'46_city_to_state_flow.html'); manifest.append((46,'City-to-state flows','46_city_to_state_flow.html'))
    p47=st[['state','salary_min','salary_max','posting_age_days','description_chars','travel_norm']].copy(); tm={k:i for i,k in enumerate(sorted(p47['travel_norm'].astype(str).unique()))}; p47['travel_num']=p47['travel_norm'].astype(str).map(tm)
    save_plotly(px.parallel_coordinates(p47,color='salary_max',dimensions=['salary_min','salary_max','posting_age_days','description_chars','travel_num'],title='47. Parallel coordinates'),out/'47_parallel_coordinates.html'); manifest.append((47,'Parallel coordinates','47_parallel_coordinates.html'))
    p48=df[['salary_min','salary_max','salary_spread','description_words','posting_age_days']].dropna(); g=sns.pairplot(p48.sample(min(120,len(p48)),random_state=42),corner=True); g.fig.suptitle('48. Pairplot numeric features',y=1.02); g.savefig(out/'48_pairplot_numeric_features.png',dpi=180); plt.close('all'); manifest.append((48,'Pairplot numeric features','48_pairplot_numeric_features.png'))
    cov_rows = []
    for c in df.columns:
        nonnull = round(100.0 * df[c].notna().mean(), 2)
        try:
            uniq = int(df[c].nunique(dropna=True))
        except TypeError:
            uniq = int(df[c].astype(str).nunique(dropna=True))
        cov_rows.append({'field': c, 'pct_populated': nonnull, 'unique_values': uniq})
    pd.DataFrame(cov_rows).sort_values('pct_populated', ascending=False).to_csv(out/'49_coverage_dashboard_table.csv', index=False); manifest.append((49,'Coverage dashboard table','49_coverage_dashboard_table.csv'))
    (out/'50_dashboard_app.py').write_text("""import pandas as pd
from dash import Dash,dcc,html,Input,Output
import plotly.express as px
CSV='50_dashboard_dataset.csv'
df=pd.read_csv(CSV)
app=Dash(__name__)
app.layout=html.Div([html.H2('50. IBM Jobs Interactive Dashboard'),dcc.Dropdown(sorted(df['state'].dropna().unique()),id='state',multi=True,placeholder='Filter state'),dcc.Dropdown(sorted(df['category'].dropna().unique()),id='category',multi=True,placeholder='Filter category'),dcc.Dropdown(sorted(df['work_type'].dropna().unique()),id='work_type',multi=True,placeholder='Filter work type'),dcc.Graph(id='map'),dcc.Graph(id='bar'),dcc.Graph(id='scatter')])
@app.callback(Output('map','figure'),Output('bar','figure'),Output('scatter','figure'),Input('state','value'),Input('category','value'),Input('work_type','value'))
def update(states,categories,work_types):
 d=df.copy()
 if states:d=d[d['state'].isin(states)]
 if categories:d=d[d['category'].isin(categories)]
 if work_types:d=d[d['work_type'].isin(work_types)]
 m=d.groupby(['state'],as_index=False).agg(job_count=('id','nunique'))
 fig_map=px.choropleth(m,locations='state',locationmode='USA-states',color='job_count',scope='usa',title='Jobs by state')
 b=d.groupby('category',as_index=False).agg(job_count=('id','nunique')).sort_values('job_count',ascending=False)
 fig_bar=px.bar(b,x='category',y='job_count',title='Jobs by category')
 fig_sc=px.scatter(d,x='posting_age_days',y='salary_mid',color='category',title='Salary vs posting age')
 return fig_map,fig_bar,fig_sc
if __name__=='__main__': app.run(debug=True)
""",encoding='utf-8')
    st[['id','state','category','work_type','salary_mid','posting_age_days']].dropna().to_csv(out/'50_dashboard_dataset.csv',index=False)
    fig=go.Figure(); c=st.groupby('category',as_index=False).agg(job_count=('id','nunique')).sort_values('job_count',ascending=False); fig.add_trace(go.Bar(x=c['category'],y=c['job_count'])); fig.update_layout(title='50. Interactive dashboard bundle (run Dash app for full filters)'); save_plotly(fig,out/'50_interactive_dashboard_bundle.html'); manifest.append((50,'Interactive dashboard app + html bundle','50_dashboard_app.py'))
    pd.DataFrame(manifest,columns=['item','name','artifact']).to_csv(out/'manifest_50_outputs.csv',index=False)

def main():
    p=argparse.ArgumentParser(description='Generate 50 IBM jobs visualizations.'); p.add_argument('--csv',default='ibm_jobs.csv'); p.add_argument('--output-dir',default='ibm_jobs_50_outputs'); a=p.parse_args()
    csv_path=Path(a.csv).resolve(); out=Path(a.output_dir).resolve(); df=prep(pd.read_csv(csv_path)); manifest,st,ct=do_all(df,out); manifest,st,ct,emb=do_more(df,out,manifest,st,ct); finish_all(df,out,manifest,st,ct,emb); df.to_csv(out/'enriched_jobs_dataset.csv',index=False)
    print(f'Input: {csv_path}'); print(f'Output: {out}'); print('Done: generated 50-item artifact set + manifest.')

if __name__=='__main__': main()
