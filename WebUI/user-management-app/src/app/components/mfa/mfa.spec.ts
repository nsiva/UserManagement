import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Mfa } from './mfa';

describe('Mfa', () => {
  let component: Mfa;
  let fixture: ComponentFixture<Mfa>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [Mfa]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Mfa);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
