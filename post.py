def writeFile(md5, hash, res):
    str = """
    <html>
        <header>
            <meta charset="utf-8">
            <title>MD5 cracker</title>
        
        </header>
        <body>
        
        <div class="container">
            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.min.css" integrity="sha384-GJzZqFGwb1QTTN6wy59ffF1BuGJpLSa9DkKMp0DgiMDm4iYMj70gZWKYbI706tWS" crossorigin="anonymous">
            <div class="jumbotron centered">
                <i class="fas fa-key fa-6x"></i>
                <h1 class="display-3">Current Password: """ + md5 + """</h1>
                <p class="secret-text">Please enter a 5-character password (a-z, A-Z)</p>
        
                <form action="/" method="POST">
        
                    <div class="form-group">
                        <input type="text" class="form-control text-center" name="md5" placeholder="5-character password (a-z, A-Z)">
                        <br>
                        <label for="picker">Please select the number of worker: </label>
                        <select class="selectpicker btn btn-outline-dark" id="picker" name="workerNum">
                            <option value=1>1</option>
                            <option value=2>2</option>
                            <option value=3>3</option>
                            <option value=4>4</option>
                            <option value=5>5</option>
                            <option value=6>6</option>
                            <option value=7>7</option>
                            <option value=8>8</option>
                            <option value=8>9</option>
                        </select>
                    </div>
        
                    <button type="submit" class="btn btn-dark">Submit</button>
                </form>
                <div class="form-group">
                    <label for="encry">MD5 hash: </label>
                    <p type="text" id="encry" class="form-control text-center" name="secret" placeholder="Encryption">""" + hash + """</p>
                </div>
                <div class="form-group">
                    <label for="decry">Decryption result: </label>
                    <p type="text" id="decry" class="form-control text-center" name="secret" placeholder="Encryption">""" + res + """</p>
                </div>
            </div>
        </div>
        </body>
        <script>
            $('.selectpicker').selectpicker('val','1');
        </script>
        
    </html>
    """
    return str