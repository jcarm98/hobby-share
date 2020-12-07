import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http'
import { Subject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private apiUrl = "https://hobbyshare.app:8000";
  private loggedInSource = new Subject<string>();

  loggedIn$ = this.loggedInSource.asObservable();

  constructor(private http: HttpClient) { }

  checkLogin(): void {
    this.http.get(this.apiUrl + "/check/login/", { responseType: 'text', withCredentials: true })
      .subscribe(response => {
        this.loggedInSource.next(response);
      });
  }

  checkUsername(username): Observable<string> {
    const fd = new FormData();
    fd.append('username', username);

    return this.http.post(this.apiUrl + "/check/username/", fd, { responseType: 'text' });
  }

  checkEmail(email): Observable<string> {
    const fd = new FormData();
    fd.append('email', email);

    return this.http.post(this.apiUrl + "/check/email/", fd, { responseType: 'text' });
  }

  signup(fname, lname, username, password, email, skills, profilePic): Observable<string> {
    const fd = new FormData();
    fd.append('fname', fname);
    fd.append('lname', lname);
    fd.append('username', username);
    fd.append('password', password);
    fd.append('email', email);

    if (profilePic !== undefined) {
      fd.append('profilepic', profilePic, profilePic.name);
    }

    fd.append('skills', JSON.stringify(skills));

    return this.http.post(this.apiUrl + "/sign-up/", fd, { responseType: 'text' });
  }

  verify(token): Observable<string> {
    const fd = new FormData();
    fd.append('token', token);

    return this.http.post(this.apiUrl + "/verify/user/", fd, { responseType: 'text' });
  }

  login(username, password): Observable<string> {
    const fd = new FormData();
    fd.append("username", username);
    fd.append("password", password);

    return this.http.post(this.apiUrl + "/log-in/", fd, { responseType: 'text', withCredentials: true });
  }

  logout(): Observable<string> {
    return this.http.post(this.apiUrl + "/log-out/", "", { responseType: 'text', withCredentials: true });
  }

  contact(subject, email, message): Observable<string> {
    const fd = new FormData();
    fd.append("subject", subject);
    fd.append("from", email);
    fd.append("message", message);

    return this.http.post(this.apiUrl + "/email/", fd, {responseType: 'text'});
  }

  forgotUsername(email): Observable<string> {
    const fd = new FormData();
    fd.append("email", email);

    return this.http.post(this.apiUrl + "/forgot/username/", fd, {responseType: 'text'});
  }

  forgotPassword(username): Observable<string> {
    const fd = new FormData();
    fd.append("username", username);

    return this.http.post(this.apiUrl + "/forgot/password/", fd, { responseType: 'text' });
  }

  resetPassword(token, password): Observable<string> {
    const fd = new FormData();
    fd.append("token", token);
    fd.append("password", password);

    return this.http.post(this.apiUrl + "/reset/password/", fd, { responseType: 'text'});
  }

  fetchUsername(): Observable<string> {
    return this.http.get(this.apiUrl + "/fetch/username/", { responseType: 'text', withCredentials: true });
  }

  getUser(username): Observable<string> {
    return this.http.get(this.apiUrl + "/user/" + username + "/", { responseType: 'text', withCredentials: true });
  }

  getSelf(): Observable<string> {
    return this.http.get(this.apiUrl + "/self/", { responseType: 'text', withCredentials: true });
  }

  patchUser(fname, lname, username, email, password, newpassword, profilePic, skills): Observable<string> {
    const fd = new FormData();
    fd.append("method", "PATCH");
    if (password !== undefined) {
      fd.append("password", password);
    }

    if (fname !== undefined) {
      fd.append('fname', fname);
    }

    if (lname !== undefined) {
      fd.append('lname', lname);
    }

    if (username !== undefined) {
      fd.append('username', username);
    }

    if (email !== undefined) {
      fd.append('email', email);
    }

    if (newpassword !== undefined) {
      fd.append('newpassword', newpassword);
    }

    if (profilePic !== undefined) {
      fd.append('profilepic', profilePic, profilePic.name);
    }

    if (skills !== undefined) {
      fd.append('skills', JSON.stringify(skills));
    }

    return this.http.post(this.apiUrl + "/user/", fd, { responseType: 'text', withCredentials: true });
  }

  deleteUser(password): Observable<string> {
    const fd = new FormData();
    fd.append("method", "DELETE");

    if (password !== undefined) {
      fd.append("password", password);
    }

    return this.http.post(this.apiUrl + "/user/", fd, { responseType: 'text', withCredentials: true });
  }

  createProject(name, purpose, plan, skills, res1, res2): Observable<string> {
    const fd = new FormData();
    if (name !== undefined) {
      fd.append("name", name);
    }

    if (purpose !== undefined) {
      fd.append("purpose", purpose);
    }

    if (plan !== undefined) {
      fd.append("plan", plan);
    }

    fd.append("status", "Planning");

    if (res1 !== undefined) {
      fd.append('res1', res1, res1.name);
    }
    if (res2 !== undefined) {
      fd.append('res2', res2, res2.name);
    }

    fd.append('skills', JSON.stringify(skills));

    return this.http.post(this.apiUrl + "/project/", fd, { responseType: 'text', withCredentials: true });
  }

  getProject(id): Observable<string> {
    return this.http.get(this.apiUrl + "/project/" + id + "/", { responseType: 'text', withCredentials: true });
  }

  fetchProjectId(): Observable<string> {
    return this.http.get(this.apiUrl + "/fetch/lastproject/", { responseType: 'text', withCredentials: true });
  }

  invite(username, id): Observable<string> {
    const fd = new FormData();
    fd.append("username", username);
    fd.append("id", id);
    return this.http.post(this.apiUrl + "/invite/", fd, { responseType: 'text', withCredentials: true });
  }

  join(id): Observable<string> {
    const fd = new FormData();
    fd.append("id", id);
    return this.http.post(this.apiUrl + "/request/", fd, { responseType: 'text', withCredentials: true });
  }

  leave(id): Observable<string> {
    const fd = new FormData();
    fd.append("id", id);
    return this.http.post(this.apiUrl + "/leave/", fd, { responseType: 'text', withCredentials: true });
  }

  fetchProjects(ids): Observable<string> {
    const fd = new FormData();
    fd.append("ids", ids);
    return this.http.post(this.apiUrl + "/fetch/projects/", fd, {responseType: 'text'});
  }

  recent(): Observable<string> {
    return this.http.get(this.apiUrl + "/recent/", { responseType: 'text'});
  }

  patchProject(id, name, purpose, plan, skills, status, res1, res2): Observable<string> {
    const fd = new FormData();
    fd.append("method", "PATCH");

    if (name !== undefined) {
      fd.append("name", name);
    }

    if (purpose !== undefined) {
      fd.append("purpose", purpose);
    }

    if (plan !== undefined) {
      fd.append("plan", plan);
    }

    if (skills !== undefined) {
      fd.append("skills", JSON.stringify(skills));
    }

    if (status !== undefined) {
      fd.append("status", status);
    }

    if (res1 !== undefined) {
      fd.append("res1", res1, res1.name);
    }

    if (res2 !== undefined) {
      fd.append("res2", res2, res2.name);
    }

    return this.http.post(this.apiUrl + "/project/" + id + "/", fd, { responseType: 'text', withCredentials: true });

  }

  deleteProject(id): Observable<string> {
    const fd = new FormData();
    fd.append("method", "DELETE");
    return this.http.post(this.apiUrl + "/project/" + id + "/", fd, { responseType: 'text', withCredentials: true });
  }

  removeContributor(id, username): Observable<string> {
    const fd = new FormData();
    fd.append("id", id);
    fd.append("username", username);
    return this.http.post(this.apiUrl + "/remove/", fd, { responseType: 'text', withCredentials: true });
  }
}
