import pandas as pd
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
