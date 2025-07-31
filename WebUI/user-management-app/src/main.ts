import { platformBrowser } from '@angular/platform-browser';
import { App } from './app/app';
import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { routes } from './app/app-routing-module'; // You need to create this


bootstrapApplication(App, {
    providers: [
        provideHttpClient(),
        provideRouter(routes)
    ]
}).catch((err) => console.error(err));
