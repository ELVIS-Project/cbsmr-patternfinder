const URLPARAMS = new URLSearchParams(window.location.search)
const ace = require('ace-builds');

const searchBoilerplate = 
`**kern
*clefG2
*k[]
=-
`;

var EDITOR;
var vrvToolkit = new verovio.toolkit();

function newResultDiv(occ, svg) {
	// Div wrapper
	var resultDiv = document.createElement("div")
	resultDiv.classList.add("occurrence")
	var resultPage = document.getElementById("resultPage")
	resultPage.appendChild(resultDiv)

	// SVG container
	svgSpan = document.createElement("span")
	svgSpan.innerHTML = svg
	resultDiv.appendChild(svgSpan)

	// piece id span
	var pidSpan = document.createElement("span")
	pidSpan.innerHTML = occ["pid"];
	resultDiv.appendChild(pidSpan)
};

function renderSvgFromBase64Xml(xmlBase64) {
	vrvToolkit = new verovio.toolkit();

	var options = {
		inputFormat: "xml",
		scale: 40,
		font: "Leipzig",
		adjustPageHeight: 1,
		noFooter: 1,
		noHeader: 1
	}
	vrvToolkit.setOptions(options)
	xml = window.atob(xmlBase64)
	var svg = vrvToolkit.renderData(xml, options);
	return svg
}

function renderQuery(krn) {
	vrvToolkit = new verovio.toolkit();

	var options = {
		scale: 40,
		font: "Leipzig",
		adjustPageHeight: 1,
		noFooter: 1,
		noHeader: 1
	}
	vrvToolkit.setOptions(options)

	var svg = vrvToolkit.renderData(krn, options);
	return svg
}

function setQuery(krn) {
	/* -> updates hidden form field
	 * -> renders verovio
	 */
	var svgContainer = document.getElementById("humdrum-viewer");
	svgContainer.innerHTML = renderQuery(krn);
	document.forms["search"].elements["query"].value = krn;
}

function uncollapseKrn(krn) {
	vertical = krn.replace(new RegExp(" ", "g"), "\n");
	horizontal = vertical.replace(new RegExp(",", "g"), " ");
	return horizontal
}

function ProcessResponse(searchResponse) {
	EDITOR.setValue(searchResponse['query'])
	setQuery(searchResponse['query']);

	for (i = 0; i < searchResponse['rpp']; i++) {
		occJson = JSON.parse(searchResponse['pages'][URLPARAMS.get('page')][i])
		if (occJson['excerptFailed']) {
			console.log("excerpt failed: " + occJson)
		} else {
			svg = renderSvgFromBase64Xml(occJson['xmlBase64'])
			newResultDiv(occJson, svg)
		}
	} 
}

function newAceEditor() {
	EDITOR = ace.edit("ace-editor", {
		autoScrollEditorIntoView: true,
		value: this.input,
		minLines: 10,
		maxLines: 10
	});

	EDITOR.setValue(searchBoilerplate);

	// rerender the svg-container on change
	EDITOR.session.on('change', function(delta){
		setQuery(EDITOR.getValue())
	});
}

function getSearchBar() {
	return document.getElementById("search-bar");
}

function setSearchFormDefaults() {
	form = document.forms["search"]
	form.elements["rpp"].value = "5";
	form.elements["page"].value = "0";
}

(() => {
	console.log("did change");
	newAceEditor();
	setSearchFormDefaults();

	var searchResponse = JSON.parse(document.getElementById("searchResponse").innerHTML)
	if (Object.values(searchResponse).length !== 0)  {
		ProcessResponse(searchResponse)
	}
})();


/*
function NewFlatEditor() {
	console.log("initiating flat editor")
	var container = document.getElementById('flat-embed');
	//container.innerHTML = `<iframe src="https://flat-embed.com/5c95a76645d83371f2c5029f" height="450" width="100%" frameBorder="0" allowfullscreen></iframe>`
  var embed = new Flat.Embed(container, {
    score: '5cb402588411a64ef7c90b82',
    embedParams: {
      appId: '5c95a7dff2ef0871dba762b9',
      controlsFloating: true,
			mode: 'edit'
    }
  });
	embed.focusScore().then(function() {})
}
*/

/*
const redux = require('redux')
const pagination = require('pagination')

let resultStore = redux.createStore(resultCounter)

function resultCounter(state = {count: 0, cur: ""}, action) {
    switch (action.type) {
        case 'NEW':
            state['count']++
            state['cur'] = action.svg
            return state
        default:
            return state
    }
}

for (i = 0; i < urlParams.get('rpp'); i++) {
    console.log(i)
    reqParams = new URLSearchParams()
   reqParams.set('pid', searchResponse['pages'][urlParams.get('page')][i]['pid'])
    reqParams.set('nid', searchResponse['pages'][urlParams.get('page')][i]['nid'])
    var url = new URL("http://localhost/excerpt")
    for (key of reqParams.keys()) {
        url.searchParams.set(key, reqParams.get(key))
    }
    console.log(url)
    var headers = new Headers()
    headers.append("content-type", "text/xml")
    //var req = new Request(searchResponse['pages'][urlParams.get('page')], {
    var req = new Request(url, {
        method: 'GET',
        headers: headers,
        mode: 'no-cors'
    })
    console.log(req)
    fetch(req)
        .then(response => response.text())
        .then(str => {

            // Render results
            var options = {
                scale: 40,
                font: "Leipzig",
                adjustPageHeight: 1,
                noFooter: 1,
                noHeader: 1
            }
            vrvToolkit.setOptions(options)
            var svg = vrvToolkit.renderData(str, options);
            resultStore.dispatch({type:'NEW', svg: svg})
        });
}

function setResultHtml(i, svg) {
    document.getElementById('result-' + i).innerHTML = svg
}

resultStore.subscribe(() => setResultHtml(resultStore.getState()['count'], resultStore.getState()['cur']))

//var paginator = new pagination.SearchPaginator({prelink:'/search', current: urlParams.get('page'), rowsPerPage: urlParams.get('rpp'), totalResult: searchResults['total']});
//console.log(paginator.render());

*/
/*
var bootstrapPaginator = new pagination.TemplatePaginator({
    prelink:'/', current: 3, rowsPerPage: 200,
    totalResult: 10020, slashSeparator: true,
    template: function(result) {
        var i, len, prelink;
        var html = '<div><ul class="pagination">';
        if(result.pageCount < 2) {
            html += '</ul></div>';
            return html;
        }
        prelink = this.preparePreLink(result.prelink);
        if(result.previous) {
            html += '<li class="page-item"><a class="page-link" href="' + prelink + result.previous + '">' + this.options.translator('PREVIOUS') + '</a></li>';
        }
        if(result.range.length) {
            for( i = 0, len = result.range.length; i < len; i++) {
                if(result.range[i] === result.current) {
                    html += '<li class="active page-item"><a class="page-link" href="' + prelink + result.range[i] + '">' + result.range[i] + '</a></li>';
                } else {
                    html += '<li class="page-item"><a class="page-link" href="' + prelink + result.range[i] + '">' + result.range[i] + '</a></li>';
                }
            }
        }
        if(result.next) {
            html += '<li class="page-item"><a class="page-link" href="' + prelink + result.next + '" class="paginator-next">' + this.options.translator('NEXT') + '</a></li>';
        }
        html += '</ul></div>';
        return html;
    }
})
//document.getElementById("paging").innerHTML = paginator.render();

(function() {
    var paginator = new pagination.ItemPaginator({prelink:'/excerpt', pageParamName: "pieceId", current: 3, rowsPerPage: 200, totalResult: 10020});
    var html = paginator.render();
    var paginator = pagination.create('search', {prelink:'/excerpt', current: 1, rowsPerPage: 200, totalResult: 10020});
    html += paginator.render();
    document.getElementById("paging").innerHTML = html;
})();
*/
