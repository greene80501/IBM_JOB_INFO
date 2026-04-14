
  var careerSearchScope ={scopeid: 'careers2'};
  var careerSearchAppId ={appid: 'careers'};
  var lang = {language: 'zz'};
  var language = document.getElementsByName('languageCode')[0].content;
  var Jsonlocation = language+".json";
  var noResultsMessage = {msg: 'Can\x27t find a job that would be a good fit? Join our [talent network|https:\/\/careers.ibm.com\/en_US\/globalform?source=WEB_Search_NA] or set up a [job alert|https:\/\/careers.ibm.com\/en_US\/careers\/JobAlerts] and we\x27ll keep you up to date with career opportunities and stories that match your interests.'};
  var url = window.location.origin+"/content/dam/adobe-cms/translations/career/careers_embed_labels_"+Jsonlocation;
  var careerSearchdata = fetch(url).then((resp) => {
                          if (resp.ok) {
                            return resp.json();
                          } else {
                            deafaultAPI();
                          }
                        })
                        .then((obj) => {
                          if(obj)
                          translation(obj);
                        })
                        .catch((error) => {
                          console.error('Language specific JSON not found defaulting to English');
                        });
  searchKey = {...searchKey,careerSearchScope,careerSearchAppId,lang,noResultsMessage};

  function deafaultAPI(){
    var Jsonlocation = "en.json";
    var url = window.location.origin+"/content/dam/adobe-cms/translations/career/careers_embed_labels_"+Jsonlocation;
    fetch(url).then((resp) => {
        if (resp.ok) {
        return resp.json();
        } else {
        deafaultAPI();
        }
    })
    .then((obj) => {
      if(obj)
        careerSearch(obj);
    })
    .catch((error) => {
        console.error('Language specific JSON not found defaulting to English');
    });
  }

  function translation(obj){
    searchKey={...searchKey,obj};
    var translations ={
                      "Remote": obj.career.value["Show-remote-only"],
                      "Show remote only": obj.career.value["Show-remote-only"],  
					  "Hybrid": obj.career.value["Hybrid"],					  
                      "Software Engineering": obj.career.value["Software-Engineering"],
                      "Consulting": obj.career.value.Consulting,
                      "Infrastructure & Technology": obj.career.value["Infrastructure-Technology"],
                      "Project Management": obj.career.value["Project-Management"],
                      "Product Management": obj.career.value["Product-Management"],
                      "Data & Analytics": obj.career.value["Data-Analytics"],
                      "Enterprise Operations": obj.career.value["Enterprise-Operations"],
					  "Japanese only": obj.career.value["Show-Japanese"],
                      "Sales": obj.career.value.Sales,
                      "Cloud": obj.career.value.Cloud,
                      "Research": obj.career.value.Research,
                      "Design & UX": obj.career.value["Design-UX"],
                      "Security": obj.career.value.Security,
                      "Others": obj.career.value.Others,       
                      "Professional": obj.career.value.Professional,
                      "Entry Level": obj.career.value["Entry-level"],
                      "Intern": obj.career.value.Internship,
					  "Internship": obj.career.value.Internship,
                      "Algeria": obj.career.value.Algeria,
                      "Argentina": obj.career.value.Argentina,
                      "Australia": obj.career.value.Australia,
                      "Austria": obj.career.value.Austria,
                      "Bangladesh": obj.career.value.Bangladesh,
                      "Belgium": obj.career.value.Belgium,
                      "Brazil": obj.career.value.Brazil,
                      "Bulgaria": obj.career.value.Bulgaria,
                      "Canada": obj.career.value.Canada,
                      "Chile": obj.career.value.Chile,
                      "China": obj.career.value.China,
                      "Colombia": obj.career.value.Colombia,
                      "Costa Rica": obj.career.value["Costa-Rica"],
                      "Croatia": obj.career.value.Croatia,
                      "Cyprus": obj.career.value.Cyprus,
                      "Czech Republic": obj.career.value["Czech-Republic"],
                      "Denmark": obj.career.value.Denmark,
                      "Ecuador": obj.career.value.Ecuador,
                      "Egypt": obj.career.value.Egypt,
                      "Finland": obj.career.value.Finland,
                      "France": obj.career.value.France,
                      "Germany": obj.career.value.Germany,
                      "Ghana": obj.career.value.Ghana,
                      "Greece": obj.career.value.Greece,
                      "Hong Kong": obj.career.value["Hong-Kong"],
                      "Hungary": obj.career.value.Hungary,
                      "India": obj.career.value.India,
                      "Indonesia": obj.career.value.Indonesia,
                      "Ireland": obj.career.value.Ireland,
                      "Israel": obj.career.value.Israel,
                      "Italy": obj.career.value.Italy,
                      "Japan": obj.career.value.Japan,
                      "Kenya": obj.career.value.Kenya,
                      "Latvia": obj.career.value.Latvia,
                      "Lithuania": obj.career.value.Lithuania,
                      "Malaysia": obj.career.value.Malaysia,
                      "Mexico": obj.career.value.Mexico,
                      "Morocco": obj.career.value.Morocco,
                      "Netherlands": obj.career.value.Netherlands,
                      "New Zealand": obj.career.value["New-Zealand"],
                      "Nigeria": obj.career.value.Nigeria,
                      "Norway": obj.career.value.Norway,
                      "Pakistan": obj.career.value.Pakistan,
                      "Peru": obj.career.value.Peru,
                      "Philippines": obj.career.value.Philippines,
                      "Poland": obj.career.value.Poland,
                      "Portugal": obj.career.value.Portugal,
                      "Qatar": obj.career.value.Qatar,
                      "Romania": obj.career.value.Romania,
                      "Saudi Arabia": obj.career.value["Saudi-Arabia"],
                      "Serbia": obj.career.value.Serbia,
                      "Singapore": obj.career.value.Singapore,
                      "Slovakia": obj.career.value.Slovakia,
                      "Slovenia": obj.career.value.Slovenia,
                      "South Africa": obj.career.value["South-Africa"],
                      "Korea": obj.career.value["South-Korea"],
                      "Spain": obj.career.value.Spain,
                      "Sri Lanka": obj.career.value["Sri-Lanka"],
                      "Sweden": obj.career.value.Sweden,
                      "Switzerland": obj.career.value.Switzerland,
                      "Taiwan": obj.career.value.Taiwan,
                      "Thailand": obj.career.value.Thailand,
                      "Tunisia": obj.career.value.Tunisia,
                      "Turkey": obj.career.value.Turkey,
                      "UAE": obj.career.value["United-Arab-Emirates"],
                      "United Kingdom": obj.career.value["United-Kingdom"],
                      "United States": obj.career.value["United-States"],
                      "Uruguay": obj.career.value.Uruguay,
                      "Venezuela": obj.career.value.Venezuela,
                      "Vietnam": obj.career.value.Vietnam,
                  }
      if(translations){
        var data = JSON.parse(document.getElementById("__NEXT_DATA__").innerHTML);
        var pageProps = data.props.pageProps;
        var existingObject = pageProps[1];
        
        existingObject["translation-content"] = {
          ...existingObject["translation-content"],
          ...translations,
        };
        pageProps[1] = existingObject;
        document.getElementById("__NEXT_DATA__").innerHTML = JSON.stringify(data);
      }
    }
