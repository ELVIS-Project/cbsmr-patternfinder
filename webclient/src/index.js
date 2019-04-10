const redux = require('redux')
const pagination = require('pagination')
const urlParams = new URLSearchParams(window.location.search)

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

/*
function NewResultDiv(id) {
	var resultPage = document.GetElementById("resultsPage")
	var resultDiv = document.CreateElement("div")


var searchResponse = {
    pages: [
        [{pid: 4020, nid: "0,1,2,3"},
        {pid: 4020, nid: "12,13,14,15"},
        {pid: 4020, nid: "13,21"},
        {pid: 4020, nid: "24,25,26,27,28"},
        {pid: 4020, nid: "7"}]
    ],
    total: 5
}
	*/
var searchResponse = JSON.parse(document.getElementById("searchResponse").innerHTML)

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
            var vrvToolkit = new verovio.toolkit();

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

/*
const flat = require('flat-embed')

var container = document.getElementById('flat-embed');
var embed = new flat.Embed(container, {
    score: '5c95a76645d83371f2c5029f',
    embedParams: {
        appId: '5c95a7dff2ef0871dba762b9',
        controlsFloating: false
    }
})

*/
