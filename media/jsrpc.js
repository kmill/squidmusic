// jsrpc.js

jsrpc = new (function() {
    function method(url, name) {
      this.run = function(args, success, error) {
        success = success || (function () {});
        error = error || (function () {});
        function handleSuccess(res) {
          if ("result" in res) {
            success(res["result"]);
          } else if ("error" in res) {
            error(res["error"]);
          } else {
            error("Malformed result");
          }
        }
        function handleError(jqxhr, txt, error) {
          error([txt, error]);
        }
        var data = {method : name,
                    kwargs : args || {}};
        
        $.ajax({url : url,
                type : "GET",
                data : {message : JSON.stringify(data)},
                dataType : "json",
                timeout : 5000,
                success : handleSuccess,
                error : handleError});
      }
    }
    this.module = function(url) {
      return new function() {
        this.method = function(name) {
          return new method(url, name);
        };
      };
    };
  })();
