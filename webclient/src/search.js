import './search.css';
import 'bootstrap/dist/css/bootstrap.min.css';

const URLPARAMS = new URLSearchParams(window.location.search)
const pagination = require('pagination');
const ace = require('ace-builds');

const searchBoilerplate = 
`**kern
*clefG2
*k[]
=-
`;

var ACE_EDITOR;

function newResultDiv(occ, svg) {
	// Div wrapper
	var resultDiv = document.createElement("div")
	resultsDiv.classList.add("occurrence")
	var resultsContainer = document.getElementById("results-container")
	resultsContainer.appendChild(resultDiv)

	// SVG container
	var svgSpan = document.createElement("span")
	svgSpan.innerHTML = svg
	resultDiv.appendChild(svgSpan)

	// piece id span
	var pidSpan = document.createElement("span")
	pidSpan.classList.add("occurrence-pid")
	pidSpan.innerHTML = occ["pid"];
	resultDiv.appendChild(pidSpan);

	var pathSpan = document.createElement("span")
	pathSpan.innerHTML = occ["path"];
	resultDiv.appendChild(pathSpan);
};

function renderSvgFromBase64Xml(xmlBase64) {
	var vrvToolkit = new verovio.toolkit();

	var options = {
		inputFormat: "xml",
		scale: 40,
		font: "Leipzig",
		adjustPageHeight: 1,
		noFooter: 1,
		noHeader: 1
	}
	vrvToolkit.setOptions(options)
	var xml = window.atob(xmlBase64)
	var svg = vrvToolkit.renderData(xml, options);
	return svg
}

function renderQuery(krn) {
	var vrvToolkit = new verovio.toolkit();

	var options = {
		scale: 60,
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
	var vertical = krn.replace(new RegExp(" ", "g"), "\n");
	var horizontal = vertical.replace(new RegExp(",", "g"), " ");
	return horizontal
}

function ProcessResponse(searchResponse) {
	ACE_EDITOR.setValue(searchResponse['query'])
	
	// Svg Container
	setQuery(searchResponse['query']);

	//newPaginator(searchResponse);

	// Render Excerpts
	for (var i = 0; i < searchResponse['rpp']; i++) {
		var occJson = JSON.parse(searchResponse['pages'][URLPARAMS.get('page')][i])
		if (occJson['excerptFailed']) {
			console.log("excerpt failed: " + occJson)
		} else {
			var svg = renderSvgFromBase64Xml(occJson['xmlBase64'])
			document.getElementById("occ-" + i.toString()).innerHTML = svg
		}
	} 
}

function newPaginator(searchResponse) {
	var pageCount = searchResponse["pageCount"]
	var curPage = searchResponse["page"]

	var pageNumbers = calculatePageNumberRange(5, curPage, pageCount)

	// Generate buttons
	var buttonsDiv = document.getElementById("results-paginator-links");
	for (var i = pageNumbers[0]; i < pageNumbers.length; i++) {

		var pageLink = newPaginatorLink(i, i);

		if (i == curPage - 1) {
			var previousLink = newPaginatorLink(i, "previous");
			previousLink.classList.add("previous");
			buttonsDiv.appendChild(previousLink);
		}
		if (i == curPage) {
			pageLink.classList.add("current");
		}
		if (i == curPage + 1 ) {
			var nextLink = newPaginatorLink(i, "next");
			nextLink.classList.add("next");
			buttonsDiv.appendChild(nextLink);
		}

		buttonsDiv.appendChild(pageLink);
	}
}

function newPaginatorLink(pageNum, html) {
	URLPARAMS.set("page", pageNum);
	var elt = document.createElement("a");
	elt.href = URLPARAMS.toString();
	elt.innerHTML = html;
	return elt
}

function calculatePageNumberRange(num, cur, total) {
	var pageNumbers = [...Array(num).keys()].map(i => i + 1) // indexed from 1, not 0
	if (total - cur < 3) {
		pageNumbers = pageNumbers.map(i => i + total - num)
	} else if (cur > 2) {
		pageNumbers = pageNumbers.map(i => i + Math.floor(cur / 2))
	}
	return pageNumbers
}

function newAceEditor() {
	ACE_EDITOR = ace.edit("ace-editor", {
			autoScrollEditorIntoView: true,
			value: searchBoilerplate,
			minLines: 10,
			maxLines: 10
	});

	// rerender the svg-container on change
	ACE_EDITOR.session.on('change', function(delta){
		setQuery(ACE_EDITOR.getValue())
	});
}

function setSearchForm(rpp, page) {
	var form = document.forms["search"]
	form.elements["rpp"].value = rpp;
	form.elements["page"].value = page;
}

(() => {
	newAceEditor();
	setSearchForm(5, 0);

	var searchResponse = JSON.parse(document.getElementById("searchResponse").innerHTML)
	//var searchResponse = {pageCount: URLPARAMS.get('pageCount'), page: URLPARAMS.get('page'), rpp: URLPARAMS.get('rpp'), query: URLPARAMS.get('query')}

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
