import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, CommonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  transactions: any[] = [];
  linkToken: string | null = null;
  itemId: string | null = null;

  constructor(private http: HttpClient) {}

  createLinkToken() {
    this.http
      .post<any>('http://localhost:5000/api/create_link_token', {})
      .subscribe((res) => {
        this.linkToken = res.link_token;
        this.openPlaidLink();
      });
  }

  openPlaidLink() {
    if (!this.linkToken) return;

    const handler = (window as any).Plaid.create({
      token: this.linkToken,
      onSuccess: (public_token: string) => {
        console.log('Public Token:', public_token);
        this.exchangePublicToken(public_token);
      },
      onExit: (err: any, metadata: any) => {
        console.error('Plaid exit:', err, metadata);
      },
    });

    handler.open();
  }

  exchangePublicToken(publicToken: string) {
    this.http
      .post<any>('http://localhost:5000/api/exchange_public_token', {
        public_token: publicToken,
      })
      .subscribe((res) => {
        console.log('Access token stored:', res);
        this.itemId = res.item_id;
        this.getTransactions();
      });
  }

  getTransactions() {
    const url = `http://localhost:5000/api/transactions?item_id=${this.itemId}`;
    this.http.get<any>(url).subscribe((res) => {
      this.transactions = res.transactions;
      console.log('Transactions:', this.transactions);
    });
  }
}
