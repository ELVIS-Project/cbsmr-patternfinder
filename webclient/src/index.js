const redux = require('redux')
const pagination = require('pagination')
const urlParams = new URLSearchParams(window.location.search)

console.log("ch")

var searchResponse = {
    pages: [
        {pid: 4020, nid: "0,1,2,3"},
        {pid: 4020, nid: "12,13,14,15"},
        {pid: 4020, nid: "13,21"},
        {pid: 4020, nid: "24,25,26,27,28"},
        {pid: 4020, nid: "7"}
    ],
    total: 5
}

for (var i = 0; i < urlParams.get('rpp'); i++) {
    reqParams = new URLSearchParams()
    reqParams.set('q', urlParams.get('q'))
    reqParams.set('rpp', urlParams.get('rpp'))
    reqParams.set('page', urlParams.get('page'))

    reqParams.set('pid', searchResponse['pages'][urlParams.get('page')]['pid'])
    reqParams.set('nid', searchResponse['pages'][urlParams.get('page')]['nid'])
    var headers = new Headers()
    headers.append("content-type", "application/xml")
    var url = new URL("http://localhost/excerpt")
    for (key of reqParams.keys()) {
        url.searchParams.set(key, reqParams.get(key))
    }
    console.log(url)
    var req = new Request(url, {
        method: 'GET',
        headers: headers,
        mode: 'no-cors'
    })
    fetch(req)
        .then(function(resp) {
            var vrvToolkit = new verovio.toolkit();

            // Render results
            options = {
                scale: 40,
                pageHeight: 1200
            }
            vrvToolkit.setOptions(options)
            var svg = vrvToolkit.renderData(resp.text, {});
            setResultHtml(0, svg)
            console.log(svg)
        });
}

function setResultHtml(i, svg) {
    document.getElementById('result-' + i).innerHTML = svg
}

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