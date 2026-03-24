import sqlite3, hashlib, os
passwordSalt = '5lo' # Arbritary but hopefully vaguely unqiue! It means pre computed hases are kaput


def connectDB(database):
    try:
        conn = sqlite3.connect(database)
        conn.execute("PRAGMA foreign_keys = 1") # why this isn't the default is beyond me, enabling foreign keys.
        conn.commit()
        cursor = conn.cursor()
        return conn, cursor
    except:
        print("Failed to connect to the database!")
        return False


def makeTables(conn, cursor):
    queries = [
        "CREATE TABLE IF NOT EXISTS Publications(publishYear YEAR NOT NULL, sourceTitle VARCHAR(255) NOT NULL, journalString VARCHAR(100) NOT NULL, doiURL VARCHAR(100) NOT NULL PRIMARY KEY, pathToPDF VARCHAR(255), pageNumbers VARCHAR(50), volume VARCHAR(20), issue VARCHAR(20) );",
        "CREATE TABLE IF NOT EXISTS Authors(authorID INTEGER PRIMARY KEY AUTOINCREMENT, fullName VARCHAR(255))",
        "CREATE TABLE IF NOT EXISTS publicationAuthors (doiURL VARCHAR(100) NOT NULL, authorID INTEGER NOT NULL, authorOrder INTEGER NOT NULL, PRIMARY KEY(doiURL, authorID), UNIQUE(doiURL, authorOrder), FOREIGN KEY (doiURL) REFERENCES Publications(doiURL) ON DELETE CASCADE, FOREIGN KEY (authorID) REFERENCES Authors(authorID) ON DELETE CASCADE)",
        "CREATE TABLE IF NOT EXISTS Administrators(username VARCHAR(255) NOT NULL PRIMARY KEY, password VARCHAR(256) NOT NULL);"
    ]
    for query in queries:
        try:
            cursor.execute(query)
        except Exception as e:
            print(f"Failed to create tables, Error: {e}")
            quit()
    conn.commit()


class Publication:
    def __init__(self, authors, publishYear, sourceTitle, journalString, doiURL, pathToPDF, pageNumbers, volume, issue):
        self._authors = authors
        self._publishYear = publishYear
        self._sourceTitle = sourceTitle
        self._journalString = journalString
        self._doiURL = doiURL
        self._pathToPDF = pathToPDF
        self._pageNumbers = pageNumbers
        self._volume = volume
        self._issue = issue
    def generateCitation(self):
        authors = self.getAuthorString()
        year = self.getPublishYear()
        title = self.getSourceTitle()
        journal = self.getJournalString()
        volume = self.getVolume()
        issue = self.getIssue()
        pages = self.getPageNumbers()
        doi = self.getDoiURL()

        citation = f"{authors} ({year}). {title}. {journal}"

        # Only add volume, issue, and pages if they exist
        if volume:
            citation += f", {volume}"
            if issue:
                citation += f"({issue})"
        if pages:
            citation += f", {pages}"

        citation += f". {doi}"

        return citation
    #Getters
    def getAuthorString(self):
        if not self._authors:
            return ""

        if len(self._authors) == 1:
            return self._authors[0]

        if len(self._authors) == 2:
            return self._authors[0] + " & " + self._authors[1]

        # Three or more authors
        authorString = ""
        for i in range(len(self._authors)):
            if i == len(self._authors) - 1:
                # Last author
                authorString += "& " + self._authors[i]
            else:
                # Not last author
                authorString += self._authors[i] + ", "
        return authorString
    def getAuthors(self):
        return self._authors
    def getPublishYear(self):
        return int(self._publishYear)
    def getSourceTitle(self):
        return self._sourceTitle
    def getJournalString(self):
        return self._journalString
    def getDoiURL(self):
        return self._doiURL
    def getPathToPDF(self):
        return self._pathToPDF
    def getPageNumbers(self):
        return self._pageNumbers
    def getVolume(self):
        return self._volume
    def getIssue(self):
        return self._issue
    #Setters
    def setAuthors(self, authors):
        self._authors = authors
    def setPublishYear(self, publishYear):
        self._publishYear = publishYear
    def setSourceTitle(self, sourceTitle):
        self._sourceTitle = sourceTitle
    def setJournalString(self, journalString):
        self._journalString = journalString
    def setDoiURL(self, doiURL):
        self._doiURL = doiURL
    def setPathToPDF(self, pathToPDF):
        self._pathToPDF = pathToPDF
    def setPageNumbers(self, pageNumbers):
        self._pageNumbers = pageNumbers
    def setVolume(self, volume):
        self._volume = volume
    def setIssue(self, issue):
        self._issue = issue


class Administrator:
    def __init__(self, username, password):
        self._username = username.lower()
        self._password = password
    def getUsername(self):
        return self._username
    def getPassword(self):
        return self._password
    def setUsername(self, username):
        self._username = username.lower()
    def setPassword(self, password):
        self._password = password


def hash(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()


def createAdmin(conn, cursor, admin):
    try:
        username = admin.getUsername()
        hashedPassword = hash(admin.getPassword(), passwordSalt)
        cursor.execute("INSERT INTO Administrators VALUES (? , ?);", (username, hashedPassword))
        conn.commit()
    except Exception as e:
        print("Database query failed!", e)
        return False
    return True


def newAdminOnboard(conn, cursor):
    print("-----------------------")
    print("Administrator Management")
    username = getValidatedCLIInput('username', "What will the new admin's username be?: ")
    password = getValidatedCLIInput('password', "What will the new admin's password be?: ")
    admin = Administrator(username, password)
    if createAdmin(conn, cursor, admin):
        print(f"Succesfully created admin with username {username}!")
    else:
        print("Failed to create admin!")


def validateCredentials(admin, conn, cursor):
    try:
        username = admin.getUsername()
        hashedPassword = hash(admin.getPassword(), passwordSalt)
        cursor.execute("SELECT * FROM Administrators WHERE username = ? COLLATE NOCASE AND password = ?;", (username, hashedPassword))
        return not (len(cursor.fetchall()) == 0)
    except:
        print("Database lookup failed!")
        return False


def dateInsertionSort(publications): # Descending order
    for index in range(1, len(publications)):
        current = publications[index]
        position = index

        while position > 0 and publications[position - 1].getPublishYear() < current.getPublishYear():
            publications[position] = publications[position - 1]
            position -= 1

        publications[position] = current

    return publications


def binarySearch(publications, query): # Descending order
    found = False
    middle = -1
    start = 0
    end = len(publications)-1
    while (found == False) and (start <= end):
        middle = ((start+end) // 2)
        if publications[middle].getPublishYear() == query:
            found = True
        elif publications[middle].getPublishYear() > query:
            start = middle + 1
        else:
            end = middle -1
    return found, middle


def validateInput(dataType, value):
    dataType = str(dataType).lower()

    match dataType:
        case 'authorsn':
            if len(value) <= 0 or not value.isdigit():
                raise ValueError("The number of authors cannot be empty or non integer!")
            return int(value)
     
        case 'author':
            if len(value) > 255 or len(value) <= 0:
                raise ValueError("The author's name cannot be longer than 255 characters or empty!")
            return value.replace("’", "'") # there's two different apostrophes that citations like using, this makes sure that this doesn't end up with duplicated authors

        case 'publishyear':
            if (not len(value) == 4) or not value.isdigit():
                raise ValueError("The publishYear must be exactly 4 characters and cannot be non-numeric!")
            return int(value)

        case 'sourcetitle':
            if len(value) > 255 or len(value) <= 0:
                raise ValueError("The publication title cannot be longer than 255 characters or empty!")
            return value

        case 'journalstring':
            if len(value) > 100 or len(value) <= 0:
                raise ValueError("journalString cannot be longer than 100 characters or empty!")
            return value

        case 'doiurl':
            value = value.lower()
            if not value.startswith("https://") or len(value) > 100 or len(value) <= 0:
                raise ValueError("DOI must start with 'https://' and be <= 100 characters and cannot be empty")
            return value

        case 'pdf':
            if len(value) > 255:
                raise ValueError("PDF Path cannot be longer than 255 characters!")
            return value
        
        case 'pagenumbers':
            if len(value) > 50:
                raise ValueError("Page numbers string cannot be longer than 50 characters")
            return value

        case 'volume':
            if len(value) > 20:
                raise ValueError("Volume string cannot be longer than 20 characters!")
            return value

        case 'issue':
            if len(value) > 20:
                raise ValueError("Issue string cannot be longer than 20 characters!")
            return value

        case 'username':
            if len(value) > 255 or len(value) <= 0:
                raise ValueError("Your username cannot be longer than 255 characters or empty!")
            return value

        case 'password':
            if len(value) > 256 or len(value) <= 0:
                raise ValueError("Your password cannot be longer than 256 characters or empty!")
            return value


def getValidatedCLIInput(dataType, prompt):
    while True:
        user_input = input(prompt)
        try:
            return validateInput(dataType, user_input)
        except ValueError as e:
            print(e)


def publicationWizard(): # Ideally this should be able to parse pre made APA citations but like whatevs
    print("-----------------------")
    print("Publication Wizard!")
    authorsn = getValidatedCLIInput("authorsn", "Please enter how many authors were cited on this publication: ")
    authors = []
    for i in range(authorsn):
        authors.append(getValidatedCLIInput("author", f"Please enter author #{i+1}'s APA formatted full name: "))
    publishYear = getValidatedCLIInput("publishYear", "Please enter the year this publication was published: ")
    sourceTitle = getValidatedCLIInput("sourcetitle", "Please enter the title of the publication: ")
    journalString = getValidatedCLIInput("journalstring", "Please enter the name of the Journal: ")
    doiURL = getValidatedCLIInput("doiurl", "Please enter the DOI of the publication, including https:// : ")
    PDF = getValidatedCLIInput("pdf", "Please enter the path to the PDF relative to the current working directory, if not applicable then leave blank! : ")
    pageNumbers = getValidatedCLIInput("pagenumbers", "Please enter the pages of the journal formatted like '22-26' or like 'Article 74', if not applicable then leave blank! : ")
    volume = getValidatedCLIInput("volume", "Please enter the volume of the publication, if not applicable then leave blank! : ")
    issue = getValidatedCLIInput("issue", "Please enter the issue of the publication, if not applicable then leave blank! : ")
    publication = Publication(authors, publishYear, sourceTitle, journalString, doiURL, PDF, pageNumbers, volume, issue)
    return publication


def insertPublication(conn, cursor, publication):
    try:
        # Insert into Publications table
        query = "INSERT INTO Publications VALUES (?,?,?,?,?,?,?,?);"
        cursor.execute(query, (publication.getPublishYear(), publication.getSourceTitle(), publication.getJournalString(), publication.getDoiURL(), publication.getPathToPDF(), publication.getPageNumbers(), publication.getVolume(), publication.getIssue()))

        # Insert authors and link them
        authors = publication.getAuthors()

        for i in range(len(authors)):
            authorName = authors[i]

            # Check if author already exists
            cursor.execute("SELECT authorID FROM Authors WHERE fullName = ?;", (authorName,))
            data = cursor.fetchone()

            if data:
                authorID = data[0]
            else:
                cursor.execute("INSERT INTO Authors (fullName) VALUES (?);", (authorName,))
                authorID = cursor.lastrowid

            # Link author to publication
            cursor.execute("INSERT INTO PublicationAuthors (doiURL, authorID, authorOrder) VALUES (?, ?, ?);", (publication.getDoiURL(), authorID, i + 1))

        conn.commit()
        return True

    except:
        print("Database insertion failed!")
        return False


def insertPublications(conn, cursor, publications):
    for publication in publications:
        insertPublication(conn, cursor, publication)


def deletePublicationWizard():
    doi = getValidatedCLIInput('doiurl', "Please enter the DOI of the publication to be deleted, including https:// : ")
    return doi


def deletePublication(conn, cursor, doi):
    sql = "DELETE FROM Publications WHERE doiURL = ?;"
    try:
        cursor.execute(sql, (doi,)) # Trailing comma is necessary, otherwise python doesn't treat as a tuple and thus sqlite treats it wrong
    except:
        print("Failed to execute query!")
        return False
    conn.commit()
    return cursor.rowcount


def adminPanel(admin):
    print(f"Hello, {admin.getUsername()}")
    print("-----------------------")
    print("Admin Panel")
    print("1. Add new publication")
    print("2. Delete publication")
    print("3. Add new Administrator")
    print("4. Exit admin panel")
    print("-----------------------")
    choice = input("\n#")
    match choice:
        case '1':
            print("Adding publication")
            pub = publicationWizard()
            insertPublication(conn,cursor,pub)
            adminPanel(admin)
        case '2':
            doi = deletePublicationWizard()
            result = deletePublication(conn, cursor, doi)
            if result > 0:
                print(f"Deleted {str(result)} publications according to this query, if > 1 then duplicate entries existed.")
            else:
                print("No publications matching that DOI were found!")
            adminPanel(admin)
        case '3':
            newAdminOnboard(conn, cursor)
            adminPanel(admin)
        case '4':
            print("Exiting admin panel..")
        case _:
            print("Invalid input!")
            adminPanel(admin)


def parseDatabaseRow(row, conn, cursor):
    publishYear = row[0]
    sourceTitle = row[1]
    journalString = row[2]
    doiURL = row[3]
    pathToPDF = row[4]
    pageNumbers = row[5]
    volume = row[6]
    issue = row[7]
    sql = "SELECT Authors.fullName FROM Authors JOIN publicationAuthors ON Authors.authorID = publicationAuthors.authorID WHERE publicationAuthors.doiURL = ? ORDER BY publicationAuthors.authorOrder;"
    # Get authors
    cursor.execute(sql, (doiURL,))
    authorData = cursor.fetchall()
    authors = []
    for authorRow in authorData:
        authors.append(authorRow[0])
    return Publication(authors, publishYear, sourceTitle, journalString, doiURL, pathToPDF, pageNumbers, volume, issue)


def parseDatabaseRows(data, conn, cursor):
    publications = []
    for row in data:
        entry = parseDatabaseRow(row, conn, cursor)
        publications.append(entry)
    return publications

def loadAllPublications(conn, cursor):
    publications = []
    try:
        cursor.execute("SELECT * FROM Publications;")
        data = cursor.fetchall()
        publications = parseDatabaseRows(data, conn, cursor)
    except:
        print("Failed to perform database lookup!")
    return publications


def dropPublications(conn, cursor):
    cursor.execute("DROP TABLE Publications;")
    conn.commit()


def outputPublications(publications):
    print("-----------------------")
    for index, publication in enumerate(publications): # Fancy python for each loop that lets me keep an index
        print(f"{index+1}. {publication.generateCitation()}")
        print("-----------------------")


def searchDatabase(column, query):
    if column == 'publishYear': # So searching with binary search
        publications = loadAllPublications(conn, cursor)
        publications = dateInsertionSort(publications) # Sort the publications in memory
        results = []
        found, resulti = binarySearch(publications, query)
        while found:
            if found == True:
                results.append(publications[resulti])
                publications.pop(resulti)
            found, resulti = binarySearch(publications, query)
        if len(results) <= 0: return False
        else: return results
    # Searching with SQL instead
    if column == "Author":
        sql = "SELECT Publications.* FROM Publications JOIN PublicationAuthors ON Publications.doiURL = PublicationAuthors.doiURL JOIN Authors ON PublicationAuthors.authorID = Authors.authorID WHERE Authors.fullName = ? COLLATE NOCASE ORDER BY Publications.publishYear;"
    else:
        sql = f'SELECT * FROM Publications WHERE {column} = ? COLLATE NOCASE;'
    try:
        cursor.execute(sql, (query,)) # Trailing comma is necessary, otherwise python doesn't treat as a tuple and thus sqlite treats it wrong
        data = cursor.fetchall()
    except:
        return False
    results = parseDatabaseRows(data, conn, cursor)
    if len(results) <= 0: return False
    else: return results


def databaseSearchWizard():
    print("-----------------------")
    print("Which column would you like to search the database by?")
    print("1. Author")
    print("2. publishYear (Fast Search!)")
    print("3. sourceTitle")
    print("4. Journal")
    print("5. DOI URL")
    choice = input("\n#")
    print("Please enter your search term.")
    column = ""
    match choice:
        case '1':
            column = 'Author'
            query = getValidatedCLIInput(column, "\n#")
        case '2':
            column = 'publishYear'
            query = getValidatedCLIInput(column, "\n#")
        case '3':
            column = 'sourceTitle'
            query = getValidatedCLIInput(column, "\n#")
        case '4':
            column = 'journalString'
            query = getValidatedCLIInput(column, "\n#")
        case '5':
            column = 'doiURL'
            query = getValidatedCLIInput(column, "\n#")
        case _:
            print("Please enter a valid column!")
            databaseSearchWizard()
    results = searchDatabase(column, query)
    if results:
        outputPublications(results)
    else:
        print("No publications matching your query were found!")


def main():
    print("-----------------------")
    print("Academic Database")
    print("1. View database sorted by date published descending")
    print("2. Login as an Admin")
    print("3. Search the database")
    print("4. Exit the program")
    print("-----------------------")
    choice = input("\n#")
    match choice:
        case '1':
            print("Sorted database")
            publications = loadAllPublications(conn, cursor)
            outputPublications(dateInsertionSort(publications))
            main()
        case '2':
            username = getValidatedCLIInput('username', "What is your username?: ")
            password = getValidatedCLIInput('password', "What is your password?: ")
            potentialAdmin = Administrator(username, password)
            if validateCredentials(potentialAdmin, conn, cursor):
                loggedIn = Administrator(username, password)
                adminPanel(loggedIn)
            else:
                print("Incorrect credentials!")
            main()
        case '3':
            databaseSearchWizard()
            main()
        case '4':
            print("Quitting...")
            quit()
        case _:
            print("Invalid input!")
            main()


# Kick everything off!
database = 'database.db'
firstRun = not (os.path.exists(database))
value = connectDB(database)
if not (value == False):
    conn, cursor = value
else:
    print("Failed to connect to the database!")
    quit()
makeTables(conn, cursor)
if firstRun:
    print("It appears this is your first time running the program, Please make an Administrator account!")
    newAdminOnboard(conn, cursor)
#loadData('2025.csv', conn, cursor)
main()
